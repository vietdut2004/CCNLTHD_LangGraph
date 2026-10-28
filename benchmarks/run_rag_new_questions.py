"""Single-attempt real Groq RAG run; no fixture or reference fed to model."""
import argparse,csv,hashlib,importlib.metadata,json,math,os,platform,socket,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
import httpx
from benchmarks.live_credentials import configure_credentials
from benchmarks.live_csv import write_results_csv

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('--cases',type=Path,required=True,help='Frozen evaluation JSON; references never go to model')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--port',type=int,default=8010)
    parser.add_argument('--delay',type=float,default=6)
    parser.add_argument('--ids',nargs='+',help='Optional subset of the supplied frozen cases; default all 8')
    args=parser.parse_args()
    credential_audit=configure_credentials(args.env_file,ROOT/'.env')
    out=(args.output or ROOT.parent/'evidence'/datetime.now(timezone(timedelta(hours=7))).strftime('live_%Y%m%d_%H%M%S')).resolve()
    out.mkdir(parents=True,exist_ok=False)
    def dump(name,data):(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    dump('credential_audit_parent.json',credential_audit)
    dataset=args.cases.resolve()
    cases=json.loads(dataset.read_text(encoding='utf-8'))['cases']
    selected=[c for c in cases if (c['id'] in args.ids if args.ids else True)]
    assert selected and (not args.ids or set(args.ids)=={c['id'] for c in selected})
    dump('test_cases.json',selected)
    env_info={'started_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
     'provider':'Groq real','model_id':os.getenv('GROQ_MODEL','openai/gpt-oss-20b'),'fixture':False,
     'credentials_present':bool(os.getenv('GROQ_API_KEY')),'requests_planned':len(selected),'concurrency':1,
     'delay_seconds':args.delay,'retries':0,'model_timeout_seconds':25,'api_deadline_seconds':60,
     'max_output_tokens':1536,'client_timeout_seconds':70,'cases_sha256':hashlib.sha256(dataset.read_bytes()).hexdigest(),
     'warmup_used':False,'first_request_includes_cold_connection_and_pdf_preparation':True,
     'packages':{p:importlib.metadata.version(p) for p in ('pypdf','langgraph','langchain-core','langchain-groq','fastapi','httpx','uvicorn','python-dotenv','pytest')}}
    dump('environment.json',env_info)
    if not os.getenv('GROQ_API_KEY'):
        dump('summary.json',{'executed':False,'blocked_reason':'CONFIG_GROQ_MISSING'})
        print('Groq key missing. No live model calls were made.');return
    with socket.socket() as sock:
        assert sock.connect_ex(('127.0.0.1',args.port))!=0,'Port already in use; no existing process stopped'
    env=dict(os.environ,RAG_CHECK_OUTPUT=str(out),RAG_CHECK_PORT=str(args.port),LANGSMITH_TRACING='false',PYTHONIOENCODING='utf-8')
    log=(out/'server.log').open('w',encoding='utf-8')
    server=subprocess.Popen([sys.executable,'-X','utf8','-m','benchmarks.serve_rag_live'],cwd=ROOT,env=env,
        stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    dump('process.json',{'server_pid':server.pid,'port':args.port})
    rows=[];stopped_reason=None
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{args.port}',timeout=70,trust_env=False,
                          transport=httpx.HTTPTransport(retries=0)) as client:
            for _ in range(60):
                if server.poll() is not None:raise RuntimeError('Server stopped; see server.log')
                try:
                    response=client.get('/openapi.json',timeout=1)
                    if response.status_code==200:
                        dump('openapi.json',response.json());dump('health.json',client.get('/health').json());break
                except httpx.TransportError:pass
                time.sleep(1)
            else:raise RuntimeError('Server readiness timeout')
            for case in selected:
                # Reference/labels are retained ONLY in the evaluator record.
                request={'question':case['question'],'mode':'rag','use_cache':False}
                row={**case,'request':request,'started_at':datetime.now(timezone.utc).isoformat()}
                start=time.perf_counter()
                try:
                    response=client.post('/chatbot',json=request)
                    row.update(http_status=response.status_code,body=response.json(),response_trace_header=response.headers.get('x-trace-id'))
                except (httpx.HTTPError,ValueError) as exc:
                    row.update(http_status=0,body={},transport_error=type(exc).__name__)
                row['latency_ms']=round((time.perf_counter()-start)*1000,3)
                row['finished_at']=datetime.now(timezone.utc).isoformat()
                traces=out/'server_traces.jsonl'
                records=[json.loads(s) for s in traces.read_text(encoding='utf-8').splitlines()] if traces.exists() else []
                row['trace']=next((r for r in reversed(records) if r['trace_id']==row['body'].get('trace_id')),None)
                row['technical_completion']=bool(row['http_status']==200 and row['body'].get('status') in ('ok','refused'))
                row['answer_returned']=bool(row['body'].get('status')=='ok')
                row['content_quality']='pending separate source audit; HTTP/citation validity is not correctness'
                rows.append(row)
                with (out/'results.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
                dump('results.json',rows)
                print(json.dumps({'case':case['id'],'http':row['http_status'],'status':row['body'].get('status'),'ms':row['latency_ms'],
                                  'tokens':row['body'].get('usage',{}).get('total_tokens')},ensure_ascii=False),flush=True)
                if row['http_status'] in (429,502,503,504) or row['http_status']==0:
                    stopped_reason=row['body'].get('code') or row.get('transport_error')
                    break  # No repeated quota/auth/network calls and no automatic retry.
                if case is not selected[-1]:time.sleep(args.delay)
    except Exception as exc:
        stopped_reason=type(exc).__name__
        dump('runner_error.json',{'type':stopped_reason})
    finally:
        if server.poll() is None:
            try:
                subprocess.run(['taskkill','/PID',str(server.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
                server.wait(timeout=5)
            except (subprocess.TimeoutExpired,PermissionError):dump('cleanup_warning.json',{'server_pid':server.pid})
        log.close()
    lat=sorted(r['latency_ms'] for r in rows);n=len(rows)
    usage=[r['body'].get('usage',{}) for r in rows]
    summary={'executed':bool(rows),'fixture':False,'n':n,'planned':len(selected),'stopped_reason':stopped_reason,
      'technical_completed':sum(r['technical_completion'] for r in rows),'technical_errors':sum(not r['technical_completion'] for r in rows),
      'answers_returned':sum(r['answer_returned'] for r in rows),'refused':sum(r['body'].get('status')=='refused' for r in rows),
      'latency_ms':{'mean':round(sum(lat)/n,3),'p50':lat[math.ceil(n*.5)-1],'p95':lat[math.ceil(n*.95)-1]} if n else None,
      'percentile_method':'nearest-rank','warmup_used':False,'usage_complete_requests':sum(u.get('usage_complete',False) for u in usage),
      'observed_tokens':{k:sum(u.get('observed_tokens',{}).get(k,0) for u in usage) for k in ('input_tokens','output_tokens','total_tokens')},
      'usage_totals':{k:sum(u.get('observed_tokens',{}).get(k,0) for u in usage) if n and all(u.get('usage_complete') is True for u in usage) else None for k in ('input_tokens','output_tokens','total_tokens')},
      'semantic_correctness':'Not inferred; see separate source audit'}
    dump('summary.json',summary)
    env_info['finished_at']=datetime.now(timezone.utc).isoformat();dump('environment.json',env_info)
    write_results_csv(out/'results.csv',rows)
    print(json.dumps({'output':str(out),'summary':summary},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
