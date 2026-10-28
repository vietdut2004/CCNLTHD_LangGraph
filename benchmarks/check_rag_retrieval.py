"""Real PDF retrieval; references are used only by the evaluator, never the retriever."""
import argparse,csv,hashlib,json,re,time
from pathlib import Path
from pypdf import PdfReader
from Rag_tool import RAGTOOL
from telemetry import identity,utc

ROOT=Path(__file__).resolve().parents[1]
def norm(s):return re.sub(r'\s+',' ',re.sub('[\uf0b7\u2022\u25cf]',' ',s)).casefold().strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',type=Path,default=ROOT/'benchmarks/rag_check_cases.json');args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    cases=json.loads(args.cases.read_text(encoding='utf-8'))['cases']
    tool=RAGTOOL();pages=[x.extract_text() or '' for x in PdfReader(tool.path).pages]
    rows=[]
    for c in cases:
        for span in c['required_spans']:
            assert any(norm(span) in norm(pages[i-1]) for i in c['reference_pages']),(c['id'],span)
        start=time.perf_counter();docs=tool.retrieve(c['question']);ms=round((time.perf_counter()-start)*1000,3)
        ranked=[]
        for rank,d in enumerate(docs,1):
            assert pages[d['page']-1][d['start']:d['end']]==d['text']
            ranked.append({'rank':rank,**d})
        coverage=[{'span':s,'matching_ranks':[d['rank'] for d in ranked if norm(s) in norm(d['text'])]} for s in c['required_spans']]
        rows.append({**c,'timestamp':utc(),'documents':ranked,'source_version':tool.version(),'retrieval_ms':ms,
          'reference_span_checks':coverage,'all_reference_spans_present':all(x['matching_ranks'] for x in coverage) if c['answerable'] else None,
          'config':{'max_chars':getattr(tool,'max_chars',650),'overlap':getattr(tool,'overlap',180),'k':tool.k,'scorer':'BM25','source_sha256':hashlib.sha256(tool.path.read_bytes()).hexdigest()}})
    groups={}
    for name in dict.fromkeys(r['group'] for r in rows):
        a=[r for r in rows if r['group']==name]
        groups[name]={'n':len(a),'answerable':sum(r['answerable'] for r in a),'all_spans_hits':sum(r['all_reference_spans_present'] is True for r in a)}
    summary={'timestamp':utc(),'provider_calls':0,'fixture':False,'scope':'real PDF lexical retrieval only; span coverage is not answer correctness',
      'cases_sha256':hashlib.sha256(args.cases.read_bytes()).hexdigest(),'groups':groups,'source_version':tool.version(),
      'identity':identity('none:offline-retrieval'),'chunk_count':len(tool.db.documents),
      'max_observed_chunk_chars':max(len(d.text) for d in tool.db.documents),'first_request_includes_index_preparation':True}
    (args.output/'results.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    with (args.output/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','group','question','reference','answerable','all_reference_spans_present','retrieval_ms'],extrasaction='ignore');w.writeheader();w.writerows(rows)
    print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
