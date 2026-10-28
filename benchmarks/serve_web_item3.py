"""Observe current real Groq/Tavily adapters without changing runtime policy."""
import json,os,time
from pathlib import Path
from agent import Agent
from searchweb_tool import SearchWebTool
from main import create_app
from telemetry import CURRENT,identity,utc
from benchmarks.web_check_credentials import audit_child
OUT=Path(os.environ['WEB_CHECK_OUTPUT'])
def write(name,data):
    t=CURRENT.get()
    with (OUT/name).open('a',encoding='utf-8') as f:f.write(json.dumps({'timestamp':utc(),'trace_id':t.trace_id if t else None,**data},ensure_ascii=False)+'\n')
class RecordedWeb(SearchWebTool):
    async def search(self,question):
        started=utc();clock=time.perf_counter();docs=await super().search(question);finished=utc()
        write('web_contexts.jsonl',{'question':question,'documents':docs,'search_started_at':started,'search_finished_at':finished,
          'search_ms':round((time.perf_counter()-clock)*1000,3),'timestamp_basis':'retrieved_at is client observation after Tavily response, not publication date'})
        return docs
class RecordedAgent(Agent):
    async def model_call(self,messages):
        reply=await super().model_call(messages)
        write('model_outputs.jsonl',{'content':reply.content,'usage':reply.usage_metadata,'response_metadata':reply.response_metadata})
        return reply
engine=RecordedAgent(web=RecordedWeb())
(OUT/'credential_audit_child.json').write_text(json.dumps(audit_child(engine),indent=2),encoding='utf-8')
(OUT/'identity.json').write_text(json.dumps(identity(engine.model_id),indent=2),encoding='utf-8')
app=create_app(engine,trace_path=OUT/'server_traces.jsonl')
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=int(os.environ['WEB_CHECK_PORT']),log_level='warning')
