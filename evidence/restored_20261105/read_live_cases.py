import json
from pathlib import Path
base=Path(__file__).resolve().parent/'faiss_live_final_13'
for line in (base/'results.jsonl').read_text(encoding='utf-8').splitlines():
 r=json.loads(line)
 print(json.dumps({'id':r['id'],'question':r['question'],'reference':r.get('reference'),
  'response':r['body'].get('response'),'status':r['body'].get('status'),
  'trace_id':r['body'].get('trace_id'),
  'evidence_checks':[e for e in (r.get('trace') or {}).get('events',[]) if e['kind']=='evidence_check'],
  'raw_model':[c.get('response_content') for c in (r.get('trace') or {}).get('model_calls',[]) if c['purpose']=='answer'],
  'sources':[{'page':s.get('page'),'quote':s.get('quote')} for s in r['body'].get('sources',[])]},ensure_ascii=False))
