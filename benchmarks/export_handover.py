import json
from pathlib import Path
from benchmarks.smoke_server import app
from telemetry import identity
out=Path('evidence_week8/handover');out.mkdir(parents=True,exist_ok=True)
g=app.state.engine.graph.get_graph()
(out/'graph_actual.json').write_text(json.dumps(g.to_json(),ensure_ascii=False,indent=2))
(out/'graph_actual.mmd').write_text(g.draw_mermaid())
(out/'selected_identity.json').write_text(json.dumps(identity('openai/gpt-oss-20b'),ensure_ascii=False,indent=2))
print('Exported actual compiled graph and configured identity; NOT a live measurement')
