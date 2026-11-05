import os,subprocess,sys
from pathlib import Path

out=Path(__file__).resolve().parent
root=out.parent/'CCNLTHD_LangGraph'
with (out/'unit_tests_light_final.log').open('w',encoding='utf-8') as log:
    result=subprocess.run([sys.executable,'-X','utf8','-m','pytest','tests','-q',
        '--basetemp='+str(out/'pytest_light_final'),
        '--junitxml='+str(out/'unit_tests_light_final.xml')],cwd=root,
        stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONIOENCODING='utf-8'))
print((out/'unit_tests_light_final.log').read_text(encoding='utf-8')[-2600:])
sys.exit(result.returncode)
