"""Offline evidence-span coverage only. Never calls an LLM or a network API."""
import argparse,csv,hashlib,json,re,time
from pathlib import Path
from pypdf import PdfReader
from Rag_tool import RAGTOOL
from retrieval import POLICY
from telemetry import identity,utc

ROOT=Path(__file__).resolve().parents[1]
def norm(text):return re.sub(r'\s+',' ',re.sub(r'[\uf0b7\u2022\u25cf]',' ',text)).casefold().strip()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--historical',type=Path,required=True);parser.add_argument('--output',type=Path,default=ROOT/'evidence_week8/retrieval');args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    old=json.loads((ROOT/'benchmarks/week8/existing_questions.json').read_text())
    spans=[['bình tĩnh và thư giãn','bộ não sẽ gửi thông điệp này'],['ngay dưới xương sườn','tay kia đặt trên ngực'],['từ 3 đến 10 lần'],['đếm thầm đến 4','đếm thầm từ 1 - 7','đếm thầm từ 1 đến 8'],['nên nằm ngửa, co đầu gối'],['trong 3 đến 5 phút'],['nâng đầu lên sau cùng'],['Tiếp tục trong 10 đến 20 phút']]
    prior=json.loads((args.historical/'results.json').read_text())
    contexts={x['trace_id']:x['documents'] for x in map(json.loads,(args.historical/'retrieval_contexts.jsonl').read_text().splitlines())}
    cases=[{'id':c['id'],'question':c['body']['question'],'reference':c['reference'],'spans':sp,'group':'existing_8'} for c,sp in zip(old,spans)]
    newpath=ROOT/'benchmarks/week8/new_questions_frozen.json';new=json.loads(newpath.read_text())
    cases += [{**c,'spans':[c['evidence']],'group':'new_6'} for c in new['cases']]
    validation_path=ROOT/'benchmarks/week8/validation_questions_frozen.json'
    cases += [{**c,'spans':[c['evidence']],'group':'validation_5'} for c in json.loads(validation_path.read_text())['cases']]
    tool=RAGTOOL();rows=[]
    for c in cases:
        started=time.perf_counter();docs=tool.retrieve(c['question']);ms=(time.perf_counter()-started)*1000
        check=lambda docs:all(any(norm(span) in norm(d['text']) for d in docs) for span in c['spans'])
        before=None
        if c['group']=='existing_8':
            trace=next(x['body']['trace_id'] for x in prior if x['case_id']==c['id']);before=check(contexts[trace])
        rows.append({**c,'timestamp':utc(),'metric':'all_reference_spans_present_at_k','k':tool.k,'evidence_hit':check(docs),'historical_embedding_top2_hit':before,'retrieval_ms':round(ms,3),'documents':docs})
    counts={g:{'n':len(a:=[x for x in rows if x['group']==g]),'hits':sum(x['evidence_hit'] for x in a)} for g in ['existing_8','new_6','validation_5']}
    summary={'recorded_at':utc(),'scope':'offline retrieval coverage, NOT model answers, clinical quality or live provider latency','provider_calls':0,'groups':counts,'historical_top2_existing_hits':sum(x['historical_embedding_top2_hit'] is True for x in rows),'historical_n':8,'current_backend':POLICY,'k':3,'source_version':tool.version(),'new_question_file_sha256':hashlib.sha256(newpath.read_bytes()).hexdigest(),'validation_file_sha256':hashlib.sha256(validation_path.read_bytes()).hexdigest(),'identity':identity('none:retrieval-only'),'limitations':['Existing 8 and additional 6 are now regression sets after the observed boundary failure; first 5/6 result preserved separately. Final validation 5 frozen before the boundary fix and evaluated once.','Both sets are AI-authored/annotated from the same small PDF; not independent human or clinical validation.','Changing chunking, ranking and k together does not isolate a single causal improvement.','A hit means source evidence is present, NOT that an LLM will answer correctly.']}
    (args.output/'results.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf8')
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    with (args.output/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','group','question','reference','evidence_hit','historical_embedding_top2_hit','retrieval_ms'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    print(json.dumps({k:summary[k] for k in ['groups','historical_top2_existing_hits','historical_n','provider_calls']},ensure_ascii=False))
if __name__=='__main__':main()
