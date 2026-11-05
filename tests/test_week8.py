import json
import os
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

@pytest.mark.skipif(os.getenv('RUN_LOCAL_EMBEDDING_TESTS')!='1',reason='Real embedding check; run the separate retrieval benchmark or opt in to avoid loading a model in unit tests')
def test_faiss_finds_requested_duration_and_keeps_source_spans():
    tool=RAGTOOL(ROOT/'Stress.pdf')
    docs=tool.retrieve('Theo Stress.pdf, bài tập tập trung vào hơi thở nên tiếp tục bao lâu?')
    assert docs and any('10 đến 20 phút' in x['text'] for x in docs)
    # Semantic top-k may contain other sections; coverage and exact provenance
    # matter here, rather than the historical BM25 section-filtering behavior.
    assert len(docs)<=tool.k
    assert [x['rank'] for x in docs]==list(range(1,len(docs)+1))
    assert all(a['score']<=b['score'] for a,b in zip(docs,docs[1:]))
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

@pytest.mark.skipif(os.getenv('RUN_LOCAL_EMBEDDING_TESTS')!='1',reason='Real embedding replay; fixture quote guards are covered separately')
def test_replayed_quote_not_in_its_cited_source_is_refused(tmp_path):
    # A quote from another passage must not validate against the cited pdf-1.
    # This does not assert that quote validation establishes answer correctness.
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
