import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from retrieval import Passage,BM25Index,passages
from Rag_tool import RAGTOOL

def test_multiple_named_sections_both_survive_top_k():
    docs=[Passage('a1',1,0,20,'1. Bài alpha','alpha alpha alpha thời lượng'),
          Passage('a2',1,21,40,'1. Bài alpha','alpha alpha thời lượng'),
          Passage('b1',2,0,20,'2. Bài beta','beta thời lượng')]
    hits=BM25Index(docs).search('So sánh thời lượng bài alpha và bài beta',k=2)
    assert {d.chunk_id for d,_ in hits}=={'a1','b1'}

@pytest.mark.parametrize('kwargs',[{'k':0},{'k':-1},{'k':True},{'max_chars':1},{'overlap':650},{'overlap':-1}])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):RAGTOOL(**kwargs)

def test_version_and_offsets_follow_actual_configuration():
    path=Path(__file__).resolve().parents[1]/'Stress.pdf'
    a=RAGTOOL(path);b=RAGTOOL(path,k=2,max_chars=500,overlap=100)
    assert a.version()!=b.version()
    docs=b.retrieve('Theo Stress.pdf, thở bụng lặp lại bao nhiêu lần?')
    assert docs and len(docs)<=2
    assert all(len(d['text'])<=500 for d in docs)
    assert all(':500:100:2' in d['source_version'] for d in docs)
    assert [d['rank'] for d in docs]==list(range(1,len(docs)+1))

def test_retrieval_order_and_scores_are_stable_across_hash_seeds():
    code="from Rag_tool import RAGTOOL; import json; print(json.dumps([(d['chunk_id'],d['score']) for d in RAGTOOL().retrieve('So sánh thở bụng và thở theo nhịp 4–7–8')]))"
    values=[subprocess.check_output([sys.executable,'-X','utf8','-c',code],env=dict(os.environ,PYTHONHASHSEED=str(seed)),text=True,encoding='utf-8') for seed in (1,42)]
    assert json.loads(values[0])==json.loads(values[1])
