import asyncio
import json
import time
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from agent import Agent
from main import create_app
from response_cache import AnswerCache
from telemetry import Trace,trace_scope
from math_graph import run_cases
from tests.fixtures_local import FixtureModel,FixtureRag,FixtureWeb

def fixture_engine(**kwargs):
    return Agent(llm=kwargs.get('llm') or FixtureModel(),rag=kwargs.get('rag') or FixtureRag(),
                 web=FixtureWeb(),model_id='fixture:no-provider')

def test_math_actual_tool_invocations(tmp_path):
    rows=run_cases(tmp_path/'math.json')
    for r in rows:
        assert [e['kind'] for e in r['trace']['events']]==['tool_start','tool_end','final']
        assert r['trace']['usage']['attempted_model_calls']==0

@pytest.mark.parametrize('mode,route,source',[('chat','answer',False),('rag','rag',True),('web','web',True)])
def test_full_trace_routes(tmp_path,mode,route,source):
    path=tmp_path/'trace.jsonl'
    with TestClient(create_app(fixture_engine(),path)) as client:
        result=client.post('/chatbot',json={'question':'Cau hoi thu nghiem','mode':mode})
    assert result.status_code==200
    body=result.json()
    assert body['status']=='ok' and body['route']==route and bool(body['sources'])==source
    trace=json.loads(path.read_text())
    assert trace['trace_id']==body['trace_id']
    assert trace['graph_id']==body['graph_id']
    kinds=[e['kind'] for e in trace['events']]
    assert kinds[0]=='classify' and kinds[-1]=='final'
    assert 'tool_start' in kinds if source else 'tool_start' not in kinds
    assert trace['suite']=='local_fixture'
    assert body['usage']['total_tokens'] is None

@pytest.mark.parametrize('question,route',[
    ('Xin chao','answer'),('Stress.pdf noi gi ve hit tho?','rag'),
    ('Tim kiem phim moi nhat','web'),('Hay ke thuoc cho toi','refuse')])
def test_auto_classification(tmp_path,question,route):
    with TestClient(create_app(fixture_engine(),tmp_path/'t')) as client:
        result=client.post('/chatbot',json={'question':question})
    assert result.json()['route']==route

@pytest.mark.parametrize('reason',['no_documents','bad_citation'])
def test_refusal_when_evidence_missing(tmp_path,reason):
    eng=fixture_engine(rag=FixtureRag(empty=reason=='no_documents'),
                       llm=FixtureModel(bad_citation=reason=='bad_citation'))
    with TestClient(create_app(eng,tmp_path/'t')) as client:
        r=client.post('/chatbot',json={'question':'Tai lieu','mode':'rag'})
    assert r.json()['status']=='refused' and r.json()['code']=='INSUFFICIENT_EVIDENCE'
    assert r.json()['sources']==[]

@pytest.mark.parametrize('payload',[{}, {'question':None}, {'question':['x']}, {'question':'  '},
                                    {'question':'x','session_id':'s'}])
def test_validation_contract(tmp_path,payload):
    with TestClient(create_app(fixture_engine(),tmp_path/'t')) as client:
        r=client.post('/chatbot',json=payload)
    assert r.status_code==422 and r.json()['code']=='INVALID_REQUEST'
    assert r.json()['usage']['attempted_model_calls']==0

class FailureModel:
    def __init__(self,error): self.error,self.calls=error,0
    async def ainvoke(self,messages):
        self.calls+=1
        raise self.error

def status_error(status):
    return httpx.HTTPStatusError('fixture',request=httpx.Request('POST','https://example.invalid'),
                                response=httpx.Response(status))

@pytest.mark.parametrize('exc,status,code',[
    (TimeoutError('fixture'),504,'UPSTREAM_TIMEOUT'),
    (status_error(429),429,'UPSTREAM_QUOTA'),
    (status_error(401),502,'UPSTREAM_AUTH'),
    (RuntimeError('unexpected'),502,'UPSTREAM_OR_GRAPH_ERROR')])
def test_provider_errors_are_not_http_200(tmp_path,exc,status,code):
    model=FailureModel(exc)
    with TestClient(create_app(fixture_engine(llm=model),tmp_path/'t')) as client:
        r=client.post('/chatbot',json={'question':'hello','mode':'chat'})
    assert r.status_code==status and r.json()['code']==code
    assert model.calls==1
    assert r.json()['usage']['total_tokens'] is None

class SlowModel:
    async def ainvoke(self,messages):
        await asyncio.sleep(1)
        return AIMessage(content='late')

def test_graph_deadline(tmp_path):
    with TestClient(create_app(fixture_engine(llm=SlowModel()),tmp_path/'t',request_timeout=.01)) as c:
        r=c.post('/chatbot',json={'question':'hello','mode':'chat'})
    assert r.status_code==504

def test_rag_exception_is_not_answer(tmp_path):
    with TestClient(create_app(fixture_engine(rag=FixtureRag(fail=True)),tmp_path/'t')) as c:
        r=c.post('/chatbot',json={'question':'tai lieu','mode':'rag'})
    assert r.status_code==503 and r.json()['code']=='RAG_SOURCE_MISSING'

def test_cache_hit_miss_user_isolation_version_and_negation(tmp_path):
    rag=FixtureRag();model=FixtureModel();engine=fixture_engine(rag=rag,llm=model)
    with TestClient(create_app(engine,tmp_path/'t')) as c:
        body={'question':'toi muon hit tho','mode':'rag','user_id':'u1','use_cache':True}
        assert c.post('/chatbot',json=body).json()['status']=='ok'
        assert rag.calls==1 and model.calls==1
        hit=c.post('/chatbot',json=body).json()
        assert hit['usage']['attempted_model_calls']==0 and rag.calls==1
        c.post('/chatbot',json={**body,'user_id':'u2'})
        assert rag.calls==2
        c.post('/chatbot',json={**body,'question':'toi KHONG muon hit tho'})
        assert rag.calls==3
        rag.revision='fixture-source-v2'
        c.post('/chatbot',json=body)
        assert rag.calls==4

def test_cache_ttl_and_capacity():
    cache=AnswerCache(ttl_seconds=-1,capacity=1)
    cache.put('a',{'answer':'a'})
    assert cache.get('a') is None
    cache=AnswerCache(capacity=1)
    cache.put('a',{});cache.put('b',{})
    assert cache.get('a') is None and cache.get('b')=={}

def test_session_context_1_2_and_other_user_isolation(tmp_path):
    model=FixtureModel();eng=fixture_engine(llm=model)
    with TestClient(create_app(eng,tmp_path/'t')) as c:
        base={'mode':'chat','user_id':'u1','session_id':'same','use_cache':True}
        c.post('/chatbot',json={**base,'question':'Toi ten la Son'})
        c.post('/chatbot',json={**base,'question':'Toi ten gi?'})
        # Human, AI from turn 1, then follow-up; proves context transmission to model adapter.
        assert len(model.contexts[-1])==4
        assert model.contexts[-1][1].content=='Toi ten la Son'
        c.post('/chatbot',json={**base,'user_id':'u2','question':'Toi ten gi?'})
        assert len(model.contexts[-1])==2
        c.post('/chatbot',json={'mode':'chat','question':'Toi ten gi?'})
        assert len(model.contexts[-1])==2
    # A new process/Agent has no persistence; no claim of durable storage.

def test_usage_unknown_and_zero_are_distinct():
    trace=Trace()
    assert trace.tokens()['total_tokens']==0
    trace.model_calls.append({'run_id':'missing','usage':None})
    assert trace.tokens()['total_tokens'] is None
    trace.model_calls=[{'run_id':'x','usage':{'input_tokens':3,'output_tokens':2,'total_tokens':5}}]*2
    assert trace.tokens()['total_tokens']==5

@pytest.mark.parametrize('missing',[None,{}])
def test_benchmark_requires_telemetry(missing):
    from benchmarks.run_evidence import grade
    case={'http':200,'status':'ok','route':'answer'}
    response={'http_status':200,'body':{'status':'ok','route':'answer','response':'ok','trace_id':'t'}}
    assert 'missing_matching_trace' in grade(case,response,missing)

class BadJsonModel:
    async def ainvoke(self,messages): return AIMessage(content='not JSON')

def test_bad_grounding_json_refuses(tmp_path):
    with TestClient(create_app(fixture_engine(llm=BadJsonModel()),tmp_path/'t')) as c:
        r=c.post('/chatbot',json={'question':'tai lieu','mode':'rag'})
    assert r.json()['status']=='refused'

def test_session_disables_cache_and_stale_sources(tmp_path):
    model=FixtureModel();eng=fixture_engine(llm=model)
    with TestClient(create_app(eng,tmp_path/'t')) as c:
        base={'user_id':'u','session_id':'s','use_cache':True}
        r=c.post('/chatbot',json={**base,'question':'tai lieu','mode':'rag'})
        assert r.json()['sources']
        r=c.post('/chatbot',json={**base,'question':'xin chao','mode':'chat'})
        assert r.json()['sources']==[] and r.json()['usage']['attempted_model_calls']==1
