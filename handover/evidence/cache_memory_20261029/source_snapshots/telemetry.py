"""Request evidence; secrets and raw exceptions are never written."""
import contextvars
import hashlib
import importlib.metadata
import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from runtime_policy import PROMPT_VERSION
from retrieval import POLICY,MAX_CHARS,OVERLAP,DEFAULT_K

CURRENT = contextvars.ContextVar('request_trace', default=None)
WRITE_LOCK = Lock()
ROOT = Path(__file__).resolve().parent

def utc():
    return datetime.now(timezone.utc).isoformat()

def identity(model):
    names = ('agent.py','main.py','Rag_tool.py','searchweb_tool.py',
             'telemetry.py','response_cache.py','math_graph.py','retrieval.py','runtime_policy.py')
    hashes = {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
              for n in names if (ROOT/n).exists()}
    versions = {}
    for name in ('langgraph','langchain-core','langchain-groq','fastapi','pypdf'):
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = None
    signature = {'source_sha256':hashes,'model_id':model,'versions':versions,
                 'prompt_version':PROMPT_VERSION,
                 'retrieval_policy':{'name':POLICY,'max_chars':MAX_CHARS,'overlap':OVERLAP,'k':DEFAULT_K},
                 'generation_policy':{'temperature':0,'max_output_tokens':1536,'timeout_seconds':25},
                 'retry_policy':{'sdk':0,'tool':0,'graph':0}}
    signature['graph_id'] = hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()[:20]
    return signature

class Trace:
    def __init__(self, model='unknown', suite='live', trace_id=None):
        self.trace_id = trace_id or uuid.uuid4().hex
        self.started_at, self.start = utc(), time.perf_counter()
        self.signature, self.suite = identity(model), suite
        self.events, self.model_calls, self.errors = [], [], []

    def event(self, event_type, **data):
        self.events.append({'timestamp':utc(),'kind':event_type,**data})

    def begin_tool(self, name, arguments):
        run_id = uuid.uuid4().hex
        self.event('tool_start',run_id=run_id,tool_name=name,arguments=arguments)
        return run_id

    def end_tool(self, run_id, name, result=None, error=None):
        self.event('tool_end',run_id=run_id,tool_name=name,result=result,error_code=error)
        if error: self.errors.append({'kind':'tool','code':error,'run_id':run_id})

    def tokens(self):
        calls = list({c['run_id']:c for c in self.model_calls}.values())
        complete = [c for c in calls if c.get('usage') and all(
            isinstance(c['usage'].get(k),int) for k in ('input_tokens','output_tokens','total_tokens'))]
        known = {k:sum(c['usage'][k] for c in complete)
                 for k in ('input_tokens','output_tokens','total_tokens')}
        return {'attempted_model_calls':len(calls),'calls_with_usage':len(complete),
                'usage_complete':len(complete)==len(calls),'observed_tokens':known,
                'total_tokens':known['total_tokens'] if len(complete)==len(calls) else None}

    def finish(self, http_status, code, route=None):
        return {'trace_id':self.trace_id,'suite':self.suite,'timestamp':self.started_at,
                **self.signature,'http_status':http_status,'code':code,'route':route,
                'server_latency_ms':round((time.perf_counter()-self.start)*1000,3),
                'events':list(self.events),'model_calls':list(self.model_calls),
                'errors':list(self.errors),'usage':self.tokens()}

def emit(kind, **data):
    trace = CURRENT.get()
    if trace: trace.event(kind,**data)

@contextmanager
def trace_scope(trace):
    token = CURRENT.set(trace)
    try: yield trace
    finally: CURRENT.reset(token)

def save(record, path=None):
    path = Path(path or os.getenv('TRACE_PATH',ROOT/'.cache'/'request_traces.jsonl'))
    path.parent.mkdir(parents=True,exist_ok=True)
    with WRITE_LOCK, path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(record,ensure_ascii=False)+'\n')
