"""In-process HTTP integration with TestClient; no external provider calls."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from benchmarks.smoke_server import app
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'evidence_week8/http';out.mkdir(parents=True,exist_ok=True)
tracepath=out/'server_traces.jsonl'
if tracepath.exists():tracepath.unlink()
with TestClient(app) as client:
    health=client.get('/health');health.raise_for_status()
    assert client.get('/').status_code==200
    identity=health.json();assert identity['fixture'] is True
    (out/'identity.json').write_text(json.dumps(identity,ensure_ascii=False,indent=2))
    cases=[('chat',{'question':'Xin chao','mode':'chat'},200,'ok'),
           ('rag',{'question':'Theo Stress.pdf, thở bụng lặp lại bao nhiêu lần?','mode':'rag'},200,'ok'),
           ('web',{'question':'FastAPI docs','mode':'web'},200,'ok'),
           ('scope',{'question':'Hãy kê thuốc','mode':'chat'},200,'refused'),
           ('validation',{},422,'error'),
           ('cache_miss',{'question':'Theo Stress.pdf, thở bụng lặp lại bao nhiêu lần?','mode':'rag','user_id':'smoke','use_cache':True},200,'ok'),
           ('cache_hit',{'question':'Theo Stress.pdf, thở bụng lặp lại bao nhiêu lần?','mode':'rag','user_id':'smoke','use_cache':True},200,'ok')]
    rows=[]
    for cid,body,status,expected in cases:
        response=client.post('/chatbot',json=body);value=response.json()
        assert response.status_code==status and value['status']==expected,(cid,value)
        assert value['graph_id']==identity['graph_id']
        if cid=='cache_hit':assert value['usage']['attempted_model_calls']==0
        rows.append({'case_id':cid,'request':body,'http_status':response.status_code,'body':value,'passed':True})
    traces=[json.loads(x) for x in tracepath.read_text().splitlines()]
    assert all(any(t['trace_id']==r['body']['trace_id'] for t in traces) for r in rows)
    (out/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    (out/'summary.json').write_text(json.dumps({'cases':len(rows),'passed':len(rows),'provider_calls':0,'fixture_llm_and_web':True,'real_local_pdf_retrieval':True,'frontend_http':200,'graph_id':identity['graph_id'],'scope':'Integration smoke only, not live Groq/Tavily or semantic quality'},ensure_ascii=False,indent=2))
    print('PASS: frontend + health + 7 HTTP cases; all joined to traces; provider calls=0')
