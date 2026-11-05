from pathlib import Path
import pytest
from retrieval import Passage,BM25Index,passages
from Rag_tool import RAGTOOL
from langchain_core.embeddings import Embeddings

class FixtureEmbeddings(Embeddings):
    """Small fixed vectors for mechanics tests, never quality evidence."""
    def embed_documents(self,texts):
        return [[len(text)/100, text.count('a')/10, text.count('e')/10] for text in texts]
    def embed_query(self,text):
        return self.embed_documents([text])[0]

@pytest.fixture
def fixture_embeddings(monkeypatch):
    monkeypatch.setattr('Rag_tool.load_embeddings',lambda *args,**kwargs:FixtureEmbeddings())

def test_multiple_named_sections_both_survive_top_k():
    docs=[Passage('a1',1,0,20,'1. Bài alpha','alpha alpha alpha thời lượng'),
          Passage('a2',1,21,40,'1. Bài alpha','alpha alpha thời lượng'),
          Passage('b1',2,0,20,'2. Bài beta','beta thời lượng')]
    hits=BM25Index(docs).search('So sánh thời lượng bài alpha và bài beta',k=2)
    assert {d.chunk_id for d,_ in hits}=={'a1','b1'}

@pytest.mark.parametrize('kwargs',[{'k':0},{'k':-1},{'k':True},{'max_chars':1},{'overlap':1000},{'overlap':-1}])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):RAGTOOL(**kwargs)

def test_version_and_offsets_follow_actual_configuration(fixture_embeddings):
    path=Path(__file__).resolve().parents[1]/'Stress.pdf'
    a=RAGTOOL(path);b=RAGTOOL(path,k=2,max_chars=500,overlap=100)
    assert a.version()!=b.version()
    docs=b.retrieve('Theo Stress.pdf, thở bụng lặp lại bao nhiêu lần?')
    assert docs and len(docs)<=2
    assert all(len(d['text'])<=500 for d in docs)
    assert all(':500:100:2' in d['source_version'] for d in docs)
    assert [d['rank'] for d in docs]==list(range(1,len(docs)+1))
    assert all(d['metric']=='squared_l2' for d in docs)
    assert all('608779b86741a8acd8c8d38132974ff04086b138' in d['source_version'] for d in docs)
    assert a.configuration()['embedding_model']=='VoVanPhuc/sup-SimCSE-VietNamese-phobert-base'
    assert a.configuration()['normalize_embeddings'] is True

def test_faiss_returns_squared_distances_and_reuses_loaded_index(fixture_embeddings):
    tool=RAGTOOL()
    first=tool.retrieve('breathing')
    db=tool.db
    second=tool.retrieve('breathing')
    assert tool.db is db
    assert first==second
    assert first[0]['score']<=first[1]['score']
    assert type(db.store.index).__name__=='IndexFlatL2'
    assert db.store.index.d==3  # Fixture dimensions, not the real model's 768.

def test_embedding_failure_is_not_replaced_with_lexical_results(monkeypatch):
    def failure(*args,**kwargs):raise RuntimeError('fixture: embedding unavailable')
    monkeypatch.setattr('Rag_tool.load_embeddings',failure)
    tool=RAGTOOL()
    with pytest.raises(RuntimeError,match='embedding unavailable'):
        tool.retrieve('stress')
    assert tool.db is None and tool.loaded_version is None
