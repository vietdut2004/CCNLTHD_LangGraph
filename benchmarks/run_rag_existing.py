"""Observe a running local demo; references never enter requests to the model."""
import json,math,platform,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
import httpx
from benchmarks.live_csv import write_results_csv

ROOT=Path(__file__).resolve().parents[1]

def run(args):
    address=urlparse(args.base_url)
    if address.hostname not in ('127.0.0.1','localhost') or address.scheme!='http':
        raise ValueError('Only an existing local HTTP demo may be observed')
    if args.output is None:
        raise ValueError('--output is required when observing an existing demo')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    def dump(name,value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def append(name,value):
        with (out/name).open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False)+'\n')
    dataset=json.loads((ROOT/'benchmarks/rag_check_cases.json').read_text(encoding='utf-8'))['cases']
    cases=[c for c in dataset if c['id'] in args.ids] if args.ids else [c for c in dataset if c['group'] in ('old_8','fresh_6','negative_2')]
    assert cases and (not args.ids or {c['id'] for c in cases}==set(args.ids))
    dump('test_cases.json',cases)
    tracepath=args.trace_file or ROOT/'.cache/request_traces.jsonl'
    rows=[];stopped=None
    with httpx.Client(base_url=args.base_url.rstrip('/'),timeout=70,trust_env=False,
                      transport=httpx.HTTPTransport(retries=0)) as client:
        health=client.get('/health').raise_for_status().json()
        if health.get('fixture'):
            raise ValueError('Live benchmark refuses a fixture server')
        prepared=health.get('rag_preparation') or {}
        if args.prepare_index and prepared.get('status')!='ready':
            raise ValueError('The existing server has not prepared its FAISS index')
        dump('health.json',health);dump('identity.json',{k:health[k] for k in (
            'graph_id','model_id','source_sha256','versions','retrieval_policy','prompt_version',
            'generation_policy','routing_policy','retry_policy')})
        dump('openapi.json',client.get('/openapi.json').raise_for_status().json())
        dump('index_preparation.json',prepared)
        environment={'started_at':datetime.now(timezone.utc).isoformat(),'fixture':False,
            'provider':'Groq real','model_id':health['model_id'],'graph_id':health['graph_id'],
            'python':platform.python_version(),'base_url':args.base_url,'server_created':False,
            'concurrency':1,'retries':0,'delay_seconds':args.delay,'warmup_used':False,
            'index_prepared_before_requests':prepared.get('status')=='ready',
            'first_request_includes_cold_connection_and_pdf_preparation':False,
            'benchmark_warmup_requests':0,
            'credentials_scope':'The running main.py reads its project .env; this client never reads or transmits API keys'}
        dump('environment.json',environment)
        if tracepath.exists():
            prior=[json.loads(s) for s in tracepath.read_text(encoding='utf-8').splitlines() if s.strip()]
            environment['prior_requests_for_active_graph']=sum(t.get('graph_id')==health['graph_id'] for t in prior)
            dump('environment.json',environment)
        for case in cases:
            request={'question':case['question'],'mode':'rag','use_cache':False}
            row={**case,'request':request,'started_at':datetime.now(timezone.utc).isoformat()}
            start=time.perf_counter()
            try:
                response=client.post('/chatbot',json=request)
                row.update(http_status=response.status_code,body=response.json(),
                    response_trace_header=response.headers.get('x-trace-id'))
            except (httpx.HTTPError,ValueError) as exc:
                row.update(http_status=0,body={},transport_error=type(exc).__name__)
            row.update(latency_ms=round((time.perf_counter()-start)*1000,3),
                       finished_at=datetime.now(timezone.utc).isoformat())
            traces=[json.loads(s) for s in tracepath.read_text(encoding='utf-8').splitlines() if s.strip()] if tracepath.exists() else []
            trace=next((t for t in reversed(traces) if t['trace_id']==row['body'].get('trace_id')),None)
            row['trace']=trace
            row['trace_joined']=trace is not None
            row['trace_graph_matches_health']=bool(trace and trace.get('graph_id')==health['graph_id'])
            row['technical_completion']=row['http_status']==200 and row['body'].get('status') in ('ok','refused')
            row['answer_returned']=row['body'].get('status')=='ok'
            row['content_quality']='Pending separate source audit; no human score generated'
            rows.append(row);append('results.jsonl',row);dump('results.json',rows)
            if trace:
                append('server_traces.jsonl',trace)
                for event in trace['events']:
                    if event['kind']=='retrieval_context':
                        append('retrieval_contexts.jsonl',{'timestamp':event['timestamp'],'trace_id':trace['trace_id'],**event})
                for call in trace['model_calls']:
                    append('model_outputs.jsonl',{'trace_id':trace['trace_id'],**call})
            print(json.dumps({'case':case['id'],'http':row['http_status'],'status':row['body'].get('status'),
                'ms':row['latency_ms'],'tokens':row['body'].get('usage',{}).get('total_tokens')},ensure_ascii=False),flush=True)
            write_results_csv(out/'results.csv',rows)
            if row['http_status'] in (0,429,502,503,504):
                stopped=row['body'].get('code') or row.get('transport_error');break
            if not row['trace_graph_matches_health']:
                stopped='MISSING_OR_DIFFERENT_SERVER_TRACE';break
            if case is not cases[-1]:time.sleep(args.delay)
    n=len(rows);lat=sorted(r['latency_ms'] for r in rows);usage=[r['body'].get('usage',{}) for r in rows]
    summary={'executed':bool(rows),'fixture':False,'n':n,'planned':len(cases),'stopped_reason':stopped,
        'technical_completed':sum(r['technical_completion'] for r in rows),
        'technical_errors':sum(not r['technical_completion'] for r in rows),
        'answers_returned':sum(r['answer_returned'] for r in rows),
        'refused':sum(r['body'].get('status')=='refused' for r in rows),
        'latency_ms':{'mean':round(sum(lat)/n,3),'p50':lat[math.ceil(n*.5)-1],'p95':lat[math.ceil(n*.95)-1]} if n else None,
        'percentile_method':'nearest-rank','usage_complete_requests':sum(u.get('usage_complete') is True for u in usage),
        'usage_totals':{k:sum(u.get('observed_tokens',{}).get(k,0) for u in usage) if n and all(u.get('usage_complete') is True for u in usage) else None
            for k in ('input_tokens','output_tokens','total_tokens')},
        'semantic_correctness':'Not inferred from HTTP status, source presence or quote matching'}
    dump('summary.json',summary);dump('unexecuted_cases.json',cases[n:])
    environment['finished_at']=datetime.now(timezone.utc).isoformat();dump('environment.json',environment)
    print(json.dumps({'output':str(out),'summary':summary},ensure_ascii=False),flush=True)
