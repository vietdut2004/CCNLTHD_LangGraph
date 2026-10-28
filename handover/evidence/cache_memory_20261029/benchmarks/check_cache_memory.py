"""Offline boundary audit; fixture adapters only, no provider calls or human scores."""
import argparse, hashlib, json, sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
a=p.parse_args();src=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(src))
from agent import Agent
from main import create_app
from response_cache import AnswerCache
import response_cache
from tests.fixtures_local import FixtureModel, FixtureRag, FixtureWeb
from fastapi.testclient import TestClient
from telemetry import identity
trace=out/'api_traces.jsonl'
if trace.exists():trace.unlink()
rows=[];checks=[]
def save(name,observed,expected):
    passed=observed==expected
    checks.append({'case':name,'observed':observed,'expected':expected,'passed':passed})
    assert passed,(name,observed,expected)
def engine():
    m,r=FixtureModel(),FixtureRag()
    return Agent(llm=m,rag=r,web=FixtureWeb(),model_id='fixture:cache-memory'),m,r
def post(c,name,payload,m,r,expected):
    mc,rc=m.calls,r.calls
    x=c.post('/chatbot',json=payload);b=x.json()
    delta={'http':x.status_code,'status':b['status'],'model_calls':m.calls-mc,'retrieval_calls':r.calls-rc}
    rows.append({'case':name,'request':payload,'response':b,'observed':delta})
    save(name,delta,expected)
    return b
ok=lambda mc,rc:{'http':200,'status':'ok','model_calls':mc,'retrieval_calls':rc}
e,m,r=engine();base={'question':'toi muon hit tho','mode':'rag','user_id':'u1','use_cache':True}
with TestClient(create_app(e,trace)) as c:
    post(c,'cache_first_miss',base,m,r,ok(1,1))
    post(c,'cache_same_key_hit',base,m,r,ok(0,0))
    post(c,'cache_normalized_case_space',{**base,'question':'  TOI  MUON HIT THO '},m,r,ok(0,0))
    post(c,'cache_changed_user',{**base,'user_id':'u2'},m,r,ok(1,1))
    post(c,'cache_added_negation',{**base,'question':'toi KHONG muon hit tho'},m,r,ok(1,1))
    r.revision='fixture-v2'
    post(c,'cache_changed_source',base,m,r,ok(1,1))
    with patch.object(response_cache,'PROMPT_VERSION','fixture-prompt-v2'):
        post(c,'cache_changed_prompt',base,m,r,ok(1,1))
    e.model_id='fixture:changed-model'
    post(c,'cache_changed_model',base,m,r,ok(1,1))
    post(c,'cache_opt_out',{**base,'use_cache':False},m,r,ok(1,1))
    post(c,'cache_anonymous',{k:v for k,v in base.items() if k!='user_id'},m,r,ok(1,1))
    post(c,'cache_session_first',{**base,'session_id':'s'},m,r,ok(1,1))
    post(c,'cache_session_second',{**base,'session_id':'s'},m,r,ok(1,1))
    # New logical caller can submit the same IDs: no authenticated principal binds them.
    post(c,'same_claimed_id_reuses_cache',base,m,r,ok(0,0))
e2,m2,r2=engine();r2.revision='fixture-v2';e2.model_id='fixture:changed-model'
with TestClient(create_app(e2,trace)) as c:
    post(c,'new_engine_has_empty_cache',base,m2,r2,ok(1,1))
# Virtual clock, not a five minute blocking wait; exact expiry boundary.
clock=[1000.0]
with patch.object(response_cache,'time',SimpleNamespace(monotonic=lambda:clock[0])):
    cache=AnswerCache();cache.put('k',{'answer':'cached'})
    clock[0]=1299.999;save('ttl_before_300_seconds',cache.get('k'),{'answer':'cached'})
    clock[0]=1300.0;save('ttl_at_300_seconds',cache.get('k'),None)
cache=AnswerCache(capacity=2);cache.put('a',{'v':1});cache.put('b',{'v':2});cache.get('a');cache.put('c',{'v':3})
save('lru_evicts_oldest_unused',cache.get('b'),None)
save('lru_retains_recent',cache.get('a'),{'v':1})
v=cache.get('a');v['v']=99;save('get_returns_copy',cache.get('a'),{'v':1})
# Check transmitted context, not whether a model understands/recalls its meaning.
e,m,r=engine();ctx=[];base={'mode':'chat','user_id':'u1','session_id':'same','use_cache':True}
def chat(c,name,q,overrides=None,expected_messages=None):
    post(c,name,{**base,'question':q,**(overrides or {})},m,r,ok(1,0))
    contents=[x.content if hasattr(x,'content') else x[1] for x in m.contexts[-1]][1:]
    ctx.append({'case':name,'transmitted_messages':contents})
    if expected_messages is not None:save(name+'_context_length',len(contents),expected_messages)
    return contents
with TestClient(create_app(e,trace)) as c:
    chat(c,'memory_first','Toi ten la Son',expected_messages=1)
    history=chat(c,'memory_followup','Toi ten gi?',expected_messages=3)
    save('history_contains_first_question',history[0],'Toi ten la Son')
    chat(c,'memory_third','luot ba',expected_messages=5)
    history=chat(c,'memory_window','luot bon',expected_messages=5)
    save('window_drops_first_turn',any('Toi ten la Son' in x for x in history),False)
    chat(c,'other_user_same_session','hoi moi',{'user_id':'u2'},1)
    chat(c,'same_user_other_session','hoi moi',{'session_id':'other'},1)
    chat(c,'without_session','hoi moi',{'session_id':None},1)
    history=chat(c,'same_claimed_ids_get_history','nguoi goi khac dung cung ID',expected_messages=5)
    save('claimed_ids_can_access_previous_context',any('luot bon' in x for x in history),True)
    invalid=c.post('/chatbot',json={'mode':'chat','question':'x','session_id':'s'})
    rows.append({'case':'session_without_user_invalid','response':invalid.json(),'http':invalid.status_code})
    save('session_without_user_http',invalid.status_code,422)
e,m,r=engine()
with TestClient(create_app(e,trace)) as c:
    chat(c,'new_engine_has_no_history','Toi ten gi?',expected_messages=1)
traces=[json.loads(x) for x in trace.read_text().splitlines()]
lookup={t['trace_id']:t for t in traces}
for row in rows:
    t=lookup[row['response']['trace_id']]
    assert t['usage']==row['response']['usage']
    if t['usage']['attempted_model_calls']:
        assert t['usage']['total_tokens'] is None # fixture has no provider usage
    else:assert t['usage']['total_tokens']==0
(out/'api_cases.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(out/'boundary_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
(out/'transmitted_contexts.json').write_text(json.dumps(ctx,ensure_ascii=False,indent=2))
summary={'identity':identity('fixture:cache-memory'),'api_requests':len(rows),'assertions':len(checks),
         'all_passed':all(x['passed'] for x in checks),'provider_calls':0,'fixture_only':True,
         'limits':['No real model memory score','IDs are caller claims, not authorization',
                   'No overall savings estimate','New-engine probe simulates in-memory lifecycle reset',
                   'TTL checked with virtual clock; no wall-clock five-minute wait',
                   'Model/prompt invalidation probes alter fixture process labels only, not runtime files']}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='identity'},ensure_ascii=False))
