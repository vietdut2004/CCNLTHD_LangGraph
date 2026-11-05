"""Tool selection mechanics with explicit model adapters; no live quality claim."""
import json
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from agent import Agent
from main import create_app
from tests.fixtures_local import FixtureModel, FixtureRag, FixtureWeb


class PlannedModel(FixtureModel):
    def __init__(self, selected_tool='rag_tool', query='a rewritten follow-up query'):
        super().__init__()
        self.selected_tool, self.query = selected_tool, query
        self.bound_options = None

    def bind_tools(self, tools, **kwargs):
        self.bound_options = kwargs
        parent = self

        class Bound:
            async def ainvoke(self, messages):
                parent.calls += 1
                parent.contexts.append(messages)
                if parent.selected_tool is None:
                    return AIMessage(content=f'fixture reply {parent.calls}')
                return AIMessage(content='', tool_calls=[{
                    'name': parent.selected_tool, 'args': {'query': parent.query},
                    'id': 'fixture-model-choice', 'type': 'tool_call',
                }])
        return Bound()


class ObservedRag(FixtureRag):
    def retrieve(self, query):
        self.last_query = query
        return super().retrieve(query)


def test_auto_executes_model_choice_and_rewritten_query_without_keywords(tmp_path):
    model, rag = PlannedModel(), ObservedRag()
    engine = Agent(llm=model, rag=rag, web=FixtureWeb(), model_id='fixture:tool-calling')
    tracepath = tmp_path/'trace.jsonl'
    with TestClient(create_app(engine, tracepath)) as client:
        result = client.post('/chatbot', json={'question': 'What about that one?', 'mode': 'auto'})
    assert result.status_code == 200 and result.json()['route'] == 'rag'
    assert rag.last_query == 'a rewritten follow-up query'
    assert model.bound_options['tool_choice'] == 'auto'
    trace = json.loads(tracepath.read_text())
    selection = next(e for e in trace['events'] if e['kind'] == 'classify')
    assert selection['policy'] == 'model-tool-calling'
    assert trace['model_calls'][0]['tool_calls'][0]['name'] == 'rag_tool'
    assert result.json()['usage']['attempted_model_calls'] == 2


def test_direct_auto_reply_is_not_generated_twice_or_reused_next_turn(tmp_path):
    model = PlannedModel(selected_tool=None)
    engine = Agent(llm=model, rag=FixtureRag(), web=FixtureWeb(), model_id='fixture:direct')
    with TestClient(create_app(engine, tmp_path/'trace')) as client:
        base = {'user_id': 'one', 'session_id': 'one'}
        first = client.post('/chatbot', json={**base, 'question': 'First greeting'}).json()
        second = client.post('/chatbot', json={**base, 'question': 'Another greeting'}).json()
    assert first['response'] == 'fixture reply 1' and second['response'] == 'fixture reply 2'
    assert model.calls == 2
    assert len(model.contexts[-1]) == 4


def test_grounded_followup_receives_real_session_history(tmp_path):
    model = FixtureModel()
    engine = Agent(llm=model, rag=FixtureRag(), web=FixtureWeb(), model_id='fixture:history')
    with TestClient(create_app(engine, tmp_path/'trace')) as client:
        base = {'user_id': 'one', 'session_id': 'one', 'mode': 'rag'}
        client.post('/chatbot', json={**base, 'question': 'The first question'})
        result = client.post('/chatbot', json={**base, 'question': 'And the next step?'})
    assert result.json()['status'] == 'ok'
    assert len(model.contexts[-1]) == 4
    assert model.contexts[-1][1].content == 'The first question'


def test_unknown_model_tool_is_an_error_without_retrieval(tmp_path):
    model, rag = PlannedModel(selected_tool='unknown_tool'), ObservedRag()
    engine = Agent(llm=model, rag=rag, web=FixtureWeb(), model_id='fixture:invalid-tool')
    with TestClient(create_app(engine, tmp_path/'trace')) as client:
        result = client.post('/chatbot', json={'question': 'A question'})
    assert result.status_code == 502
    assert result.json()['status'] == 'error' and rag.calls == 0

def test_strict_json_schema_is_used_only_for_grounded_answer(tmp_path):
    class BoundSpy(FixtureModel):
        def __init__(self):super().__init__();self.formats=[]
        def bind(self,**kwargs):self.formats.append(kwargs['response_format']);return self
    model=BoundSpy()
    engine=Agent(llm=model,rag=FixtureRag(),web=FixtureWeb(),model_id='fixture:schema')
    with TestClient(create_app(engine,tmp_path/'trace')) as client:
        grounded=client.post('/chatbot',json={'question':'tai lieu','mode':'auto'})
        direct=client.post('/chatbot',json={'question':'hello','mode':'chat'})
    assert grounded.json()['status']=='ok' and direct.json()['status']=='ok'
    assert len(model.formats)==1
    assert model.formats[0]['type']=='json_schema'
    assert model.formats[0]['json_schema']['strict'] is True

def test_provider_error_metadata_never_logs_the_key(tmp_path,monkeypatch):
    key='fixture-private-credential'
    monkeypatch.setenv('GROQ_API_KEY',key)
    class ProviderFailure(Exception):
        status_code=400
        body={'error':{'message':'invalid request '+key,'code':'fixture-error'}}
    class FailingModel:
        async def ainvoke(self,messages):raise ProviderFailure()
    path=tmp_path/'trace'
    engine=Agent(llm=FailingModel(),rag=FixtureRag(),web=FixtureWeb(),model_id='fixture:redaction')
    with TestClient(create_app(engine,path)) as client:
        response=client.post('/chatbot',json={'question':'hello','mode':'chat'})
    assert response.status_code==502
    raw=path.read_text()
    assert key not in raw
    error=json.loads(raw)['errors'][0]
    assert error['upstream_status']==400 and '[redacted]' in error['provider_message']
