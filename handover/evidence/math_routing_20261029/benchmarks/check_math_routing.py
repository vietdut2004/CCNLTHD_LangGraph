"""Offline evidence for math executor and rule router; no provider calls."""
import argparse,asyncio,hashlib,json,platform
from pathlib import Path
from langchain_core.messages import AIMessage
from fastapi.testclient import TestClient
from agent import Agent
from main import create_app
from telemetry import Trace,trace_scope,identity,utc
import math_graph

CASES=[
('auto_chat','Xin chào','auto','answer','Fallback rule; not semantic classification.'),
('auto_rag','Stress.pdf nói gì?','auto','rag','PDF keyword.'),
('auto_web','Tìm web FastAPI','auto','web','Web keyword.'),
('overlapping_keywords','Tìm web tài liệu FastAPI','auto','rag','Known limitation: RAG keywords precede WEB keywords; not semantic intent recognition.'),
('auto_single_math','12 cộng 8 bằng bao nhiêu?','auto','answer','No math executor route in the chatbot.'),
('auto_math_chain','Tính (2+3)*4','auto','answer','No parser or tool-chain planning in this router.'),
('explicit_chat','Stress.pdf nói gì?','chat','answer','Explicit mode precedes RAG keyword.'),
('explicit_rag','Xin chào','rag','rag','Explicit mode selects RAG.'),
('explicit_web','Xin chào','web','web','Explicit mode selects web.'),
('scope_auto','Hãy chẩn đoán và kê thuốc','auto','refuse','Scope refusal precedes routing.'),
('scope_web','Hãy chẩn đoán và kê thuốc','web','refuse','Scope refusal precedes explicit mode.'),
('negated_web_keyword','Không tìm web, chỉ chào thôi.','auto','web','Known limitation: negated keyword still matches; NOT a semantically correct routing claim.')]
class BlockLLM:
    async def ainvoke(self,messages):raise AssertionError('classify must not invoke LLM')
class BlockRag:
    def retrieve(self,q):raise AssertionError('No RAG expected')
class BlockWeb:
    async def search(self,q):raise AssertionError('No WEB expected')
class FixtureAnswer:
    async def ainvoke(self,messages):return AIMessage(content='FIXTURE_ONLY: nhánh trả lời, không chạy công cụ toán.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    def dump(n,x):(out/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
    math_rows=math_graph.run_cases(out/'math_executor_raw.json')
    for row in math_rows:
        tr=row['trace'];assert tr['usage']['attempted_model_calls']==0
        assert [e['kind'] for e in tr['events']]==['tool_start','tool_end','final']
    dump('math_executor_scope.json',{'transport':'in-process graph.invoke, no HTTP request','warning':'http_status in raw Trace.finish is an evaluator label, not an observed API response','cases':4,'passed':4,'provider_calls':0,'llm_calls':0,'tool_selection':'Caller supplied name/arguments; not model-selected','multi_step_expression_support_proven':False})
    engine=Agent(llm=BlockLLM(),rag=BlockRag(),web=BlockWeb(),model_id='fixture:router-only')
    async def check_routes():
        rows=[]
        for cid,q,mode,expected,note in CASES:
            tr=Trace('none:router-only','direct_rule_router')
            with trace_scope(tr):result=await engine.classify({'question':q,'mode':mode})
            assert result['route']==expected,(cid,result,expected);trace=tr.finish(200,'EVALUATOR_LABEL_ONLY')
            assert trace['usage']['attempted_model_calls']==0
            rows.append({'case_id':cid,'question':q,'mode':mode,'expected_by_current_rules':expected,'observed_route':result['route'],'note':note,'trace':trace})
        return rows
    routing=asyncio.run(check_routes());dump('router_node_cases.json',routing)
    probe=Agent(llm=FixtureAnswer(),rag=BlockRag(),web=BlockWeb(),model_id='fixture:math-chain-boundary')
    with TestClient(create_app(probe,trace_path=out/'chatbot_probe_trace.jsonl')) as client:
        response=client.post('/chatbot',json={'question':'Tính (2+3)*4','mode':'auto'});body=response.json()
    trace=json.loads((out/'chatbot_probe_trace.jsonl').read_text().splitlines()[-1]);assert response.status_code==200 and body['route']=='answer'
    assert not any(e['kind']=='tool_start' for e in trace['events']);assert trace['usage']['attempted_model_calls']==1
    dump('chatbot_math_chain_probe.json',{'request':{'question':'Tính (2+3)*4','mode':'auto'},'http_status':response.status_code,'body':body,'scope':'TestClient with fixture answer; tests routing boundary, NOT math correctness or a real LLM answer','fixture_model_invocations':1,'math_tool_calls':0,'provider_calls':0})
    dump('math_graph_actual.json',math_graph.graph.get_graph().to_json());dump('chatbot_graph_actual.json',engine.graph.get_graph().to_json())
    (out/'math_graph_actual.mmd').write_text(math_graph.graph.get_graph().draw_mermaid(),encoding='utf-8')
    (out/'chatbot_graph_actual.mmd').write_text(engine.graph.get_graph().draw_mermaid(),encoding='utf-8')
    source_root=Path(math_graph.__file__).resolve().parent
    names=['agent.py','math_graph.py','main.py','telemetry.py','runtime_policy.py','Rag_tool.py','retrieval.py','response_cache.py','searchweb_tool.py']
    dump('source_hashes.json',{n:hashlib.sha256((source_root/n).read_bytes()).hexdigest() for n in names})
    dump('summary.json',{'recorded_at':utc(),'python':platform.python_version(),'provider_calls':0,'math_executor_cases':4,'math_executor_passed':4,'math_llm_calls':0,'direct_classify_cases':len(routing),'matched_implemented_rules':len(routing),'classify_llm_calls':0,'known_rule_limitation_cases':2,'chatbot_chain_probe_fixture':True,'chatbot_chain_probe_math_tool_calls':0,'scope':'Rule conformance and tool execution only; no learned tool selection, autonomous planning or end-to-end multi-step math claim'})
    print('PASS: 4 math executor cases; 12 direct rule probes; 1 fixture API boundary probe; 0 provider calls')
if __name__=='__main__':main()
