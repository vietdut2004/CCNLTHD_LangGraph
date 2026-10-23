"""Fixed cases; no retries; fixture results must never be presented as live metrics."""
import argparse
import csv
import json
import math
import platform
import time
import uuid
from pathlib import Path
import httpx
from telemetry import identity,utc

ROOT=Path(__file__).resolve().parents[1]

def percentile(values,p):
    return sorted(values)[max(0,math.ceil(len(values)*p)-1)] if values else None

def grade(case,response,trace):
    errors=[]
    if response['http_status']!=case['http']: errors.append('http_mismatch')
    body=response.get('body',{})
    if case.get('status') and body.get('status')!=case['status']: errors.append('status_mismatch')
    if case.get('route') and body.get('route')!=case['route']: errors.append('route_mismatch')
    if body.get('status')=='ok' and not body.get('response','').strip(): errors.append('empty_answer')
    if case.get('source_required') and not body.get('sources'): errors.append('missing_sources')
    if not trace or trace.get('trace_id')!=body.get('trace_id'): errors.append('missing_matching_trace')
    if trace and trace.get('graph_id')!=body.get('graph_id'): errors.append('graph_mismatch')
    if trace and case.get('cache'):
        events=[e for e in trace['events'] if e['kind']=='cache']
        if not events or events[-1]['status']!=case['cache']: errors.append('cache_mismatch')
    return errors

def run(fixture=False,base_url='http://127.0.0.1:8000',output='evidence_run',
        server_traces=None,repeat=1):
    out=Path(output)
    out.mkdir(parents=True,exist_ok=False)
    traces=out/'server_traces.jsonl' if fixture else Path(server_traces) if server_traces else None
    if not fixture and traces is None: raise ValueError('--server-traces is required to verify live results')
    cases=json.loads((ROOT/'benchmarks/cases.json').read_text(encoding='utf-8'))
    model='fixture:no-provider' if fixture else __import__('os').getenv('GROQ_MODEL','openai/gpt-oss-20b')
    if fixture:
        from fastapi.testclient import TestClient
        from main import create_app
        from agent import Agent
        from tests.fixtures_local import FixtureModel,FixtureRag,FixtureWeb
        class BenchmarkRag(FixtureRag):
            def retrieve(self,q):
                return [] if 'sinh viên' in q else super().retrieve(q)
        engine=Agent(llm=FixtureModel(),rag=BenchmarkRag(),web=FixtureWeb(),model_id=model)
        client=TestClient(create_app(engine,traces))
    else:
        client=httpx.Client(base_url=base_url,timeout=70,transport=httpx.HTTPTransport(retries=0))
    rows=[]
    session_nonce=uuid.uuid4().hex[:12]
    with client:
        warmup=client.post('/chatbot',json={'question':'Xin chào','mode':'chat'})
        (out/'warmup.json').write_text(json.dumps({'http_status':warmup.status_code,
            'body':warmup.json(),'excluded_from_summary':True},ensure_ascii=False,indent=2),encoding='utf-8')
        for turn in range(repeat):
            for case in cases:
                body=dict(case['body'])
                # Fresh users per repetition; explicit follow-up/cache cases still share their group.
                if body.get('user_id'): body['user_id']+=f'-{session_nonce}-{turn}'
                started=utc();before=time.perf_counter()
                row={'case_id':case['id'],'repeat':turn+1,'group':case['group'],'timestamp':started,
                     'suite':'local_fixture' if fixture else 'live','request':body}
                try:
                    r=client.post('/chatbot',json=body)
                    row.update(http_status=r.status_code,body=r.json())
                except (httpx.HTTPError,ValueError) as exc:
                    row.update(http_status=0,body={},transport_error=type(exc).__name__)
                row['client_latency_ms']=round((time.perf_counter()-before)*1000,3)
                trace_id=row['body'].get('trace_id')
                records=[json.loads(line) for line in traces.read_text(encoding='utf-8').splitlines()] if traces.exists() else []
                matched=[t for t in records if t['trace_id']==trace_id]
                trace=matched[-1] if matched else None
                row['trace']=trace
                row['functional_errors']=grade(case,row,trace)
                row['technical_error']=bool(row.get('transport_error') or
                    (row['body'].get('status')=='error' and case['group']!='validation') or
                    (row['http_status']>=400 and case['group']!='validation'))
                row['observable_case_pass']=not row['functional_errors']
                row['semantic_quality']=None
                row['manual_reference']=case.get('manual_reference')
                rows.append(row)
                with (out/'results.jsonl').open('a',encoding='utf-8') as f:
                    f.write(json.dumps(row,ensure_ascii=False)+'\n')
                if not fixture: time.sleep(2)
    groups={}
    for group in sorted({r['group'] for r in rows}):
        data=[r for r in rows if r['group']==group]
        lat=[r['client_latency_ms'] for r in data]
        groups[group]={'n':len(data),'technical_errors':sum(r['technical_error'] for r in data),
                       'observable_pass':sum(r['observable_case_pass'] for r in data),
                       'mean_ms':round(sum(lat)/len(lat),3),'p50_ms':percentile(lat,.5),'p95_ms':percentile(lat,.95)}
    report={'suite':'local_fixture' if fixture else 'live','timestamp':utc(),
            'model_id':model,'n':len(rows),'warmup_excluded':True,
            'groups':groups,'quality_score':None,'percentile_method':'nearest-rank',
            'warning':'Fixture latency/tokens are NOT Groq/RAG/web measurements.' if fixture else
            'Technical completion and observable checks are separate from manual semantic grading.'}
    (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'environment.json').write_text(json.dumps({'python':platform.python_version(),
        **identity(model),'sdk_retries':0,'tool_retries':0,'graph_retries':0,'client_retries':0,
        'concurrency':1,'fixture':fixture},ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'manual_grading.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['case_id','trace_id','supported_by_source_0_2','relevance_0_2',
            'scope_0_2','source_accuracy_0_2','reference','reviewer','notes'])
        for r in rows: w.writerow([r['case_id'],r['body'].get('trace_id'),'','','','',r['manual_reference'] or '','',''])
    print(json.dumps({'suite':report['suite'],'n':len(rows),
                      'observable_pass':sum(r['observable_case_pass'] for r in rows)},ensure_ascii=False))
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--fixture',action='store_true')
    p.add_argument('--base-url',default='http://127.0.0.1:8000')
    p.add_argument('--output',default='evidence_run')
    p.add_argument('--server-traces')
    p.add_argument('--repeat',type=int,default=1)
    a=p.parse_args()
    if not 1<=a.repeat<=3: p.error('--repeat must be 1..3 (up to 55 requests including warmup)')
    run(a.fixture,a.base_url,a.output,a.server_traces,a.repeat)
