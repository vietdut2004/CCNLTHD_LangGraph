"""Create derived CSVs; retain every original raw capture byte."""
import json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parent/'CCNLTHD_LangGraph'
sys.path.insert(0,str(ROOT))
from benchmarks.live_csv import write_results_csv
count=0
for folder in (BASE/'ui_restore').glob('live_conversation_*'):
 path=folder/'requests_responses.json'
 if not path.exists():continue
 records=json.loads(path.read_text(encoding='utf-8'))
 rows=[{'id':f'ui_{i+1}','question':r['request']['question'],'reference':'Historical screenshot question; no fixed model answer',
        'http_status':r.get('http_status'),'body':r.get('response') or {},
        'started_at':r['started_at'],'latency_ms':r['latency_ms_browser']} for i,r in enumerate(records)]
 write_results_csv(folder/'LIVE_RESULTS_USAGE_NORMALIZED.csv',rows)
 count+=1
print(json.dumps({'derived_csvs':count,'provider_calls':0,'raw_capture_modified':False,
 'note':'Raw LIVE_RESULTS.csv originally exported observed partial tokens. Normalized CSV leaves all token columns empty when request usage is incomplete.'}))
