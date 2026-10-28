"""Actual API and providers with sidecar observations; no replacement responses."""
import json,os,time
from pathlib import Path
from agent import Agent
from Rag_tool import RAGTOOL
from main import create_app
from telemetry import CURRENT,identity,utc
from benchmarks.live_credentials import sdk_credential_audit

OUT=Path(os.environ['RAG_CHECK_OUTPUT'])
def write(name,record):
    trace=CURRENT.get()
    with (OUT/name).open('a',encoding='utf-8') as f:
        f.write(json.dumps({'timestamp':utc(),'trace_id':trace.trace_id if trace else None,**record},ensure_ascii=False)+'\n')

class RecordedRAG(RAGTOOL):
    def retrieve(self,question):
        start=time.perf_counter();docs=super().retrieve(question)
        write('retrieval_contexts.jsonl',{'question':question,'documents':docs,'retrieval_ms':round((time.perf_counter()-start)*1000,3),
              'config':{'max_chars':self.max_chars,'overlap':self.overlap,'k':self.k},'source_version':self.loaded_version})
        return docs

class RecordedAgent(Agent):
    async def model_call(self,messages):
        reply=await super().model_call(messages)
        write('model_outputs.jsonl',{'content':reply.content,'usage':reply.usage_metadata,'response_metadata':reply.response_metadata})
        return reply

engine=RecordedAgent(rag=RecordedRAG())
(OUT/'credential_audit_child.json').write_text(json.dumps(sdk_credential_audit(engine),indent=2),encoding='utf-8')
app=create_app(engine,trace_path=OUT/'server_traces.jsonl')
(OUT/'identity.json').write_text(json.dumps(identity(engine.model_id),indent=2),encoding='utf-8')
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=int(os.environ['RAG_CHECK_PORT']),log_level='warning')
