from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib

out=Path(__file__).resolve().parent;root=out.parent/'CCNLTHD_LangGraph'
manifest=json.loads((root/'docs/RESTORED_RUNTIME_IDENTITY.json').read_text(encoding='utf-8'))
folder=out/'runtime_snapshots';folder.mkdir(exist_ok=True)
archive=folder/(manifest['identity']['graph_id']+'.zip')
if archive.exists():raise SystemExit('Snapshot already exists; preserved')
with ZipFile(archive,'w',ZIP_DEFLATED) as stream:
    for name,digest in {**manifest['identity']['source_sha256'],**manifest['frontend_sha256']}.items():
        data=(root/name).read_bytes();assert hashlib.sha256(data).hexdigest()==digest
        stream.writestr(name,data)
    for name in ['requirements.txt','requirements-locked.txt','Stress.pdf','start_api.py','docs/RESTORED_RUNTIME_IDENTITY.json']:
        stream.write(root/name,name)
print(archive.name)
