from pathlib import Path
import sys,json

root=Path(__file__).resolve().parent.parent/'CCNLTHD_LangGraph'
sys.path.insert(0,str(root))
from telemetry import identity
path=root/'docs/RESTORED_RUNTIME_IDENTITY.json'
record=json.loads(path.read_text(encoding='utf-8'))
record['identity']=identity('openai/gpt-oss-20b')
path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(record['identity']['graph_id'])
