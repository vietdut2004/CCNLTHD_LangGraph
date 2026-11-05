"""API v2: explicit error codes, request trace, scoped RAM sessions, no automatic retry."""
import asyncio
import hashlib
import json
import os
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator
from agent import Agent
from telemetry import Trace, trace_scope, save,identity,utc

load_dotenv(Path(__file__).resolve().parent/'.env',override=True)

class MessageIn(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra='forbid')
    question:str=Field(min_length=1,max_length=8000)
    mode:Literal['auto','chat','rag','web']='auto'
    user_id:str|None=Field(default=None,min_length=1,max_length=80)
    session_id:str|None=Field(default=None,min_length=1,max_length=80)
    use_cache:bool=False

    @model_validator(mode='after')
    def session_owner(self):
        if self.session_id and not self.user_id:
            raise ValueError('session_id requires user_id')
        return self

class MessageOut(BaseModel):
    response:str
    status:Literal['ok','refused','error']
    code:str
    trace_id:str
    graph_id:str
    model_id:str
    route:str|None=None
    sources:list=Field(default_factory=list)
    usage:dict=Field(default_factory=dict)


def classify_exception(exc):
    name=type(exc).__name__
    status=getattr(exc,'status_code',None)
    if status is None and getattr(exc,'response',None) is not None:
        status=exc.response.status_code
    if isinstance(exc,(TimeoutError,asyncio.TimeoutError)) or 'Timeout' in name:
        return 504,'UPSTREAM_TIMEOUT'
    if status==429: return 429,'UPSTREAM_QUOTA'
    if status in (401,403): return 502,'UPSTREAM_AUTH'
    if isinstance(exc,FileNotFoundError): return 503,'RAG_SOURCE_MISSING'
    if isinstance(exc,RuntimeError) and str(exc) in ('CONFIG_GROQ_MISSING','CONFIG_TAVILY_MISSING'):
        return 503,str(exc)
    if 'Recursion' in name: return 503,'GRAPH_STEP_LIMIT'
    return 502,'UPSTREAM_OR_GRAPH_ERROR'


def create_app(engine=None,trace_path=None,request_timeout=60):
    @asynccontextmanager
    async def lifespan(app):
        if engine is None and os.getenv('GROQ_API_KEY'):
            app.state.engine=Agent().create_agent()
            capture_runtime(app)
            start=time.perf_counter()
            record={'started_at':utc(),'provider_calls':0,'query_embedded':False}
            logging.getLogger(__name__).info('Preparing the local PDF embedding and FAISS index')
            try:
                record.update(await asyncio.to_thread(app.state.engine.rag.prepare))
                record['status']='ready'
            except Exception as exc:
                record.update(status='error',error_type=type(exc).__name__)
                logging.getLogger(__name__).warning('PDF preparation failed: %s',type(exc).__name__)
            record.update(finished_at=utc(),duration_ms=round((time.perf_counter()-start)*1000,3))
            app.state.rag_preparation=record
            path=Path(__file__).resolve().parent/'.cache'/'rag_preparation.json'
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        capture_runtime(app)
        yield
    app=FastAPI(title='Chatbot Hỗ trợ tâm lý',version='3.0-faiss',lifespan=lifespan)
    app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=False,
                       allow_methods=['GET','POST'],allow_headers=['*'])
    app.state.engine=engine
    app.state.session_locks={}
    app.state.rag_preparation=None
    app.state.runtime_identity=None
    app.mount('/frontend',StaticFiles(directory=Path(__file__).resolve().parent/'frontend'),name='frontend')

    def capture_runtime(current_app):
        # Capture the loaded runtime once; later edits on disk must not relabel
        # responses from an older process that has not been restarted yet.
        if current_app.state.runtime_identity is None:
            runner=current_app.state.engine
            model=getattr(runner,'model_id',os.getenv('GROQ_MODEL','openai/gpt-oss-20b'))
            rag=getattr(runner,'rag',None)
            config=rag.configuration() if hasattr(rag,'configuration') else None
            current_app.state.runtime_identity=identity(model,config)
        return current_app.state.runtime_identity

    @app.get('/',include_in_schema=False)
    async def frontend():
        return FileResponse(Path(__file__).resolve().parent/'frontend/index.html')

    @app.get('/health')
    async def health():
        model=getattr(app.state.engine,'model_id',os.getenv('GROQ_MODEL','openai/gpt-oss-20b'))
        rag=getattr(app.state.engine,'rag',None)
        config=rag.configuration() if hasattr(rag,'configuration') else None
        return {'service':'chatbot-ho-tro-tam-ly','configured':app.state.engine is not None or bool(os.getenv('GROQ_API_KEY')),
                'fixture':model.startswith('fixture:'),'rag_preparation':app.state.rag_preparation,**capture_runtime(app)}

    @app.middleware('http')
    async def evidence(request:Request,call_next):
        if request.url.path!='/chatbot': return await call_next(request)
        model=getattr(app.state.engine,'model_id',os.getenv('GROQ_MODEL','openai/gpt-oss-20b'))
        rag=getattr(app.state.engine,'rag',None)
        config=rag.configuration() if hasattr(rag,'configuration') else None
        trace=Trace(model,'local_fixture' if model.startswith('fixture:') else 'live',
                    retrieval_policy=config,signature=capture_runtime(app))
        request.state.trace=trace
        request.state.code='UNHANDLED_ERROR'
        request.state.route=None
        with trace_scope(trace):
            response=await call_next(request)
        record=trace.finish(response.status_code,request.state.code,request.state.route)
        save(record,trace_path)
        response.headers['X-Trace-ID']=trace.trace_id
        return response

    def error_response(request,status,code):
        trace=request.state.trace
        request.state.code=code
        return JSONResponse(status_code=status,content=MessageOut(
            response='Yeu cau chua hoan tat. Hay doi chieu trace_id de kiem tra.',
            status='error',code=code,trace_id=trace.trace_id,
            graph_id=trace.signature['graph_id'],model_id=trace.signature['model_id'],
            usage=trace.tokens()).model_dump())

    @app.exception_handler(RequestValidationError)
    async def invalid(request:Request,exc):
        # Do not echo arbitrary payloads or exception strings into logs.
        return error_response(request,422,'INVALID_REQUEST')

    @app.post('/chatbot',response_model=MessageOut,
              responses={422:{'model':MessageOut},429:{'model':MessageOut},
                         502:{'model':MessageOut},503:{'model':MessageOut},504:{'model':MessageOut}})
    async def chatbot_reply(msg:MessageIn,request:Request):
        trace=request.state.trace
        try:
            if app.state.engine is None: app.state.engine=Agent().create_agent()
            runner=app.state.engine
            state={'question':msg.question,'messages':[('human',msg.question)],
                   'mode':msg.mode,'user_id':msg.user_id or '',
                   'cache_enabled':msg.use_cache and not msg.session_id}
            config={}
            if msg.session_id:
                # Demo namespace isolation only. Caller-supplied user_id is NOT authentication.
                scope=hashlib.sha256(json.dumps([msg.user_id,msg.session_id]).encode()).hexdigest()
                if scope not in app.state.session_locks and len(app.state.session_locks)>=128:
                    return error_response(request,503,'SESSION_LIMIT')
                lock=app.state.session_locks.setdefault(scope,asyncio.Lock())
                config={'configurable':{'thread_id':scope}}
                async with asyncio.timeout(request_timeout):
                    async with lock: result=await runner.ainvoke(state,config)
            else:
                result=await asyncio.wait_for(runner.ainvoke(state,config),timeout=request_timeout)
            messages=result.get('messages',[])
            answer=getattr(messages[-1],'content','') if messages else ''
            if not isinstance(answer,str) or not answer.strip(): raise ValueError('EMPTY_ANSWER')
            route=result['route']
            request.state.route=route
            refused=bool(result.get('refusal'))
            code=('OUT_OF_SCOPE' if route=='refuse' else 'INSUFFICIENT_EVIDENCE') if refused else 'OK'
            request.state.code=code
            trace.event('final',status='refused' if refused else 'ok',code=code,
                        route=route,response=answer,sources=result.get('sources',[]))
            return MessageOut(response=answer,status='refused' if refused else 'ok',code=code,
                trace_id=trace.trace_id,graph_id=trace.signature['graph_id'],
                model_id=trace.signature['model_id'],route=route,
                sources=result.get('sources',[]),usage=trace.tokens())
        except Exception as exc:
            status,code=classify_exception(exc)
            trace.errors.append({'kind':'request','code':code,'type':type(exc).__name__})
            return error_response(request,status,code)

    return app

app=create_app()
