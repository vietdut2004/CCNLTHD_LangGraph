import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from Rag_tool import RAGTOOL
from retrieval import passages,BM25Index
from agent import Agent
from main import create_app
from tests.fixtures_local import FixtureModel,FixtureWeb

ROOT=Path(__file__).resolve().parents[1]
def test_pdf_spans_keep_offsets_and_section_boundaries():
    text='1. A\nalpha\n2. B\nbeta gamma'
    docs=passages([(1,text)],20,5)
    assert docs and all(x.text==text[x.start:x.end] for x in docs)
    assert all(not ('1. A' in x.text and '2. B' in x.text) for x in docs)
    assert any(x.section=='2. B' and 'beta' in x.text for x in docs)

def test_section_name_limits_other_exercise_and_keeps_source_span():
    tool=RAGTOOL(ROOT/'Stress.pdf')
    docs=tool.retrieve('Theo Stress.pdf, bài tập tập trung vào hơi thở nên tiếp tục bao lâu?')
    assert docs and any('10 đến 20 phút' in x['text'] for x in docs)
    assert all('Tập trung vào hơi thở' in x['section'] for x in docs)
    from pypdf import PdfReader
    pages=PdfReader(ROOT/'Stress.pdf').pages
    assert all(pages[x['page']-1].extract_text()[x['start']:x['end']]==x['text'] for x in docs)

def test_version_changes_with_pdf_bytes(tmp_path):
    path=tmp_path/'doc.pdf';path.write_bytes(b'one');tool=RAGTOOL(path);first=tool.version();path.write_bytes(b'two');assert tool.version()!=first

def test_cache_key_invalidates_on_prompt_policy_change(monkeypatch):
    import response_cache
    cache=response_cache.AnswerCache();a=cache.key('Q','u','src','model');cache.put(a,{'answer':'old'})
    monkeypatch.setattr(response_cache,'PROMPT_VERSION','different-policy')
    assert cache.get(cache.key('Q','u','src','model')) is None

def test_replay_old_wrong_section_quote_is_refused(tmp_path):
    # Captured failure pattern: answering 4-7-8 to a duration question about focus breathing.
    class Replay:
        async def ainvoke(self,messages):
            return AIMessage(content=json.dumps({'supported':True,'answer':'Đếm đến 4 khi hít vào.',
             'citations':[{'id':'pdf-1','quote':'Nín thở và đếm thầm từ 1 - 7.'}]}))
    engine=Agent(llm=Replay(),rag=RAGTOOL(ROOT/'Stress.pdf'),web=FixtureWeb(),model_id='fixture:replay')
    with TestClient(create_app(engine,tmp_path/'trace')) as client:
        r=client.post('/chatbot',json={'question':'Theo Stress.pdf, bài tập tập trung vào hơi thở nên tiếp tục bao lâu?','mode':'rag'})
        assert r.status_code==200 and r.json()['status']=='refused'
        assert r.json()['sources']==[]

def test_repo_frontend_and_health_match_response_graph(tmp_path):
    engine=Agent(llm=FixtureModel(),rag=RAGTOOL(ROOT/'Stress.pdf'),web=FixtureWeb(),model_id='fixture:handover')
    with TestClient(create_app(engine,tmp_path/'trace')) as client:
        assert client.get('/').status_code==200
        health=client.get('/health').json();assert health['fixture'] is True
        r=client.post('/chatbot',json={'question':'Xin chao','mode':'chat'}).json()
        assert r['graph_id']==health['graph_id'] and r['status']=='ok'
