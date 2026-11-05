"""Verify source, measured identities and evidence without calling providers."""
import argparse,hashlib,json,sys,importlib.metadata,re
from pathlib import Path
from telemetry import identity
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--strict',action='store_true',help='Require exact dependency versions and configured identity from measured Windows run');p.add_argument('--output',type=Path);a=p.parse_args()
 historical=json.loads((ROOT/'handover/EXPECTED_RUNTIME_IDENTITY.json').read_text(encoding='utf-8'))
 restored_path=ROOT/'docs/RESTORED_RUNTIME_IDENTITY.json'
 restored=json.loads(restored_path.read_text(encoding='utf-8')) if restored_path.exists() else None
 expected=restored['identity'] if restored else historical
 actual=identity(expected['model_id']);errors=[]
 for n,h in expected['source_sha256'].items():
  if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h:errors.append('runtime source differs: '+n)
 if restored:
  for n,h in historical['source_sha256'].items():
   old=ROOT/restored['historical_runtime_snapshot']/n
   if not old.is_file() or hashlib.sha256(old.read_bytes()).hexdigest()!=h:errors.append('historical source differs: '+n)
  for n,h in restored['frontend_sha256'].items():
   if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h:errors.append('frontend source differs: '+n)
  if hashlib.sha256((ROOT/'requirements-locked.txt').read_bytes()).hexdigest()!=restored['requirements_sha256']:
   errors.append('requirements lock differs')
  if a.strict:
   for line in (ROOT/'requirements-locked.txt').read_text(encoding='utf-8').splitlines():
    match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)',line.strip())
    if match:
     try:version=importlib.metadata.version(match[1])
     except importlib.metadata.PackageNotFoundError:version=None
     if version!=match[2]:errors.append('locked dependency differs: '+match[1])
 manifest=json.loads((ROOT/'handover/EVIDENCE_SHA256.json').read_text(encoding='utf-8'))
 for n,h in manifest.items():
  if hashlib.sha256((ROOT/'handover'/n).read_bytes()).hexdigest()!=h:errors.append('evidence differs: '+n)
 for folder in ['rag_regression_5_20261028','rag_new_8_20261028','web_4_20261028']:
  recorded=json.loads((ROOT/'handover/evidence'/folder/'identity.json').read_text(encoding='utf-8'))
  if recorded!=historical:errors.append('recorded historical identity differs: '+folder)
 version_differences={k:{'measured':v,'current':actual['versions'].get(k)} for k,v in expected['versions'].items() if v!=actual['versions'].get(k)}
 if a.strict and actual!=expected:errors.append('active runtime identity differs; install requirements-locked.txt; do not relabel historical logs')
 result={'source_and_evidence_valid':not any('source' in e or 'evidence' in e or 'recorded' in e for e in errors),
  'measured_graph_id':historical['graph_id'],'active_expected_graph_id':expected['graph_id'],
  'current_configured_graph_id':actual['graph_id'],'runtime_scope':'restored_20261105' if restored else 'historical_v1.3',
  'exact_environment_match':actual==expected,'version_differences':version_differences,'checked_evidence_files':len(manifest),
  'provider_calls':0,'strict':a.strict,'errors':errors}
 print(json.dumps(result,ensure_ascii=False,indent=2))
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return int(bool(errors))
if __name__=='__main__':sys.exit(main())
