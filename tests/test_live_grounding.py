import json
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from agent import source_quote, Agent
from main import create_app
from tests.fixtures_local import FixtureRag, FixtureWeb

def test_quote_preserves_original_span_with_pdf_whitespace():
    source='Hít vào. \n\uf0b7 Nín thở.\nThở ra.'
    assert source_quote('Hít vào. Nín thở.',source)=='Hít vào. \n\uf0b7 Nín thở.'

@pytest.mark.parametrize('quote',[
    'không nín thở đến 7','nín thở đến 8','nín thở đến 7 giây','',
])
def test_quote_does_not_accept_changed_words_numbers_or_units(quote):
    assert source_quote(quote,'nín thở đến 7') is None

def test_api_returns_original_source_quote_after_normalization(tmp_path):
    class Rag(FixtureRag):
        def retrieve(self,query):
            return [{'id':'pdf-1','title':'fixture.txt','page':1,
                     'source_version':'test','text':'Hít vào. \n\uf0b7 Nín thở.'}]
    class Model:
        async def ainvoke(self,messages):
            return AIMessage(content=json.dumps({'supported':True,'answer':'Hít vào, rồi nín thở.',
              'citations':[{'id':'pdf-1','quote':'Hít vào. Nín thở.'}]}))
    engine=Agent(llm=Model(),rag=Rag(),web=FixtureWeb(),model_id='fixture:quote')
    with TestClient(create_app(engine,tmp_path/'traces.jsonl')) as client:
        response=client.post('/chatbot',json={'question':'Tai lieu','mode':'rag'})
    assert response.status_code==200
    assert response.json()['status']=='ok'
    assert response.json()['sources'][0]['quote']=='Hít vào. \n\uf0b7 Nín thở.'
