"""Audit PhoBERT/SimCSE pooling and small chunks with genuine cached weights."""
import argparse, hashlib, json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'CCNLTHD_LangGraph'
sys.path.insert(0,str(ROOT))
from faiss_retrieval import passages, EMBEDDING_MODEL, EMBEDDING_REVISION
from pypdf import PdfReader

def norm(text):return re.sub(r'\s+',' ',re.sub('[\uf0b7\u2022\u25cf]',' ',text)).casefold().strip()

def main():
 import torch, faiss, numpy as np
 from transformers import AutoModel, AutoTokenizer
 from safetensors import safe_open
 from pyvi.ViTokenizer import tokenize
 output=Path(__file__).resolve().parent/'faiss_pooling_comparison'
 output.mkdir(exist_ok=False)
 snapshot=ROOT/'.cache/huggingface/hub'/('models--'+EMBEDDING_MODEL.replace('/','--'))/'snapshots'/EMBEDDING_REVISION
 tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True)
 model=AutoModel.from_pretrained(str(snapshot),local_files_only=True).eval()
 with safe_open(str(snapshot/'model.safetensors'),framework='pt',device='cpu') as weights:
  mlp_weight=weights.get_tensor('mlp.dense.weight')
  mlp_bias=weights.get_tensor('mlp.dense.bias')
 def embed(texts):
  arrays={name:[] for name in ('mean','cls','pooler','trained_mlp')}
  for offset in range(0,len(texts),16):
   clean=[tokenize(re.sub(r'\s+',' ',s).strip()) for s in texts[offset:offset+16]]
   inputs=tokenizer(clean,padding=True,truncation=True,max_length=256,return_tensors='pt')
   with torch.inference_mode():
    result=model(**inputs,return_dict=True)
    hidden=result.last_hidden_state
    values={'mean':(hidden*inputs['attention_mask'].unsqueeze(-1)).sum(1)/inputs['attention_mask'].sum(-1,keepdim=True),
      'cls':hidden[:,0],'pooler':result.pooler_output,
      'trained_mlp':torch.tanh(torch.nn.functional.linear(hidden[:,0],mlp_weight,mlp_bias))}
   for name,value in values.items():arrays[name].extend(value.numpy().tolist())
  return {name:np.asarray(value,dtype='float32') for name,value in arrays.items()}
 cases_file=ROOT/'benchmarks/rag_check_cases.json'
 cases=json.loads(cases_file.read_text(encoding='utf-8'))['cases']
 pages=[(i+1,p.extract_text() or '') for i,p in enumerate(PdfReader(ROOT/'Stress.pdf').pages)]
 print('Model loaded; embedding queries',flush=True)
 queries=embed([re.sub(r'^Theo\s+Stress\.pdf\s*[,;:]?\s*','',c['question'],flags=re.I) for c in cases])
 summaries=[]
 for size,overlap in [(200,50),(350,100),(500,50),(650,180)]:
  chunks=passages(pages,size,overlap)
  print('Embedding',len(chunks),'chunks',size,overlap,flush=True)
  vectors=embed([d.text for d in chunks])
  for pooling in vectors:
   matrix=vectors[pooling].copy(); query=queries[pooling].copy()
   faiss.normalize_L2(matrix);faiss.normalize_L2(query)
   index=faiss.IndexFlatL2(768);index.add(matrix)
   distances,indices=index.search(query,4)
   for k in (2,3,4):
    label=f'chunk{size}_overlap{overlap}_k{k}_pooling{pooling}'
    rows=[]
    for case,ds,ids in zip(cases,distances,indices):
     docs=[dict(chunks[int(ordinal)].__dict__,rank=rank,score=float(distance),metric='normalized_squared_l2') for rank,(distance,ordinal) in enumerate(zip(ds[:k],ids[:k]),1)]
     coverage=[{'span':s,'matching_ranks':[d['rank'] for d in docs if norm(s) in norm(d['text'])]} for s in case['required_spans']]
     rows.append(dict(case,documents=docs,span_coverage=coverage,all_spans_present=all(c['matching_ranks'] for c in coverage) if case['answerable'] else None))
    groups={}
    for group in dict.fromkeys(c['group'] for c in cases):
     members=[r for r in rows if r['group']==group]
     groups[group]={'n':len(members),'all_spans_present':sum(r['all_spans_present'] is True for r in members)}
    summary={'configuration':label,'chunk_size':size,'overlap':overlap,'k':k,'pooling':pooling,'normalize_embeddings':True,'word_segmentation':'pyvi',
      'groups':groups,'all_spans_present':sum(r['all_spans_present'] is True for r in rows),'chunk_count':len(chunks),
      'failed_answerable_ids':[r['id'] for r in rows if r['all_spans_present'] is False],'fixture':False,'provider_calls':0,
      'embedding_model':EMBEDDING_MODEL,'embedding_revision':EMBEDDING_REVISION,'strip_source_prefix':True,
      'max_input_tokens':256,'metric':'normalized_squared_l2','index_type':'IndexFlatL2'}
    (output/(label+'.json')).write_text(json.dumps(dict(summary=summary,results=rows),ensure_ascii=False,indent=2),encoding='utf-8')
    summaries.append(summary)
    print(label,summary['all_spans_present'],'/25',summary['failed_answerable_ids'],flush=True)
 manifest={'timestamp':datetime.now(timezone.utc).isoformat(),'pdf_sha256':hashlib.sha256((ROOT/'Stress.pdf').read_bytes()).hexdigest(),
   'cases_sha256':hashlib.sha256(cases_file.read_bytes()).hexdigest(),'fixture':False,'provider_calls':0,
   'scope':'real FAISS retrieval comparison; not LLM answer correctness; regression set used for tuning, not holdout',
   'modelcard':'https://huggingface.co/VoVanPhuc/sup-SimCSE-VietNamese-phobert-base',
   'simcse_implementation':'https://github.com/princeton-nlp/SimCSE/blob/main/simcse/models.py','runs':summaries}
 (output/'summary.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
