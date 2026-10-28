"""Explicit fixture LLM/web, real local PDF retriever. Not a live-provider demo."""
from pathlib import Path
from agent import Agent
from Rag_tool import RAGTOOL
from tests.fixtures_local import FixtureModel,FixtureWeb
from main import create_app
ROOT=Path(__file__).resolve().parents[1]
app=create_app(Agent(llm=FixtureModel(),rag=RAGTOOL(ROOT/'Stress.pdf'),web=FixtureWeb(),
                     model_id='fixture:week8-http'),ROOT/'evidence_week8/http/server_traces.jsonl')
