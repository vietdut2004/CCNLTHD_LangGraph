import json
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from agent import source_quote, quote_options, grounded_format, Agent
from main import create_app
from tests.fixtures_local import FixtureRag, FixtureWeb

def test_quote_preserves_original_span_with_pdf_whitespace():
    source='Hít vào. \n\uf0b7 Nín thở.\nThở ra.'
    assert source_quote('Hít vào. Nín thở.',source)=='Hít vào. \n\uf0b7 Nín thở.'

def test_typographic_quotes_match_but_return_original_source_characters():
    assert source_quote('It’s a Wonderful Life',"It's a Wonderful Life (1946)")=="It's a Wonderful Life"
    assert source_quote('"Tên phim"','“Tên phim” được đề xuất')=='“Tên phim”'

def test_typographic_normalization_does_not_remove_negation_or_change_numbers():
    assert source_quote('“Nín thở 7 giây”','“Không nín thở 8 giây”') is None

def test_schema_quote_choices_are_literal_and_avoid_unsupported_discriminators():
    documents=[{'id':'one','text':'The Movie - Tên dịch (2006)\nKhông nín thở quá lâu.'},
               {'id':'two','text':'Giữ nguyên con số 8 và đơn vị lần.'}]
    schema=grounded_format(documents)['json_schema']['schema']['properties']['citations']['items']
    assert 'anyOf' not in schema
    assert schema['properties']['id']['enum']==['one','two']
    assert schema['properties']['quote']['enum']==['one:q1','one:q2','two:q1']
    assert 'The Movie (2006)' not in quote_options(documents[0]['text'])

@pytest.mark.parametrize('source_id,quote_code,expected',[
    ('pdf-1','pdf-1:q1','ok'),('pdf-2','pdf-1:q1','refused')])
def test_selected_quote_code_resolves_only_for_its_original_source(tmp_path,source_id,quote_code,expected):
    class Rag(FixtureRag):
        def retrieve(self,query):
            return [{'id':'pdf-1','title':'fixture.txt','page':1,'source_version':'test','text':'Nín thở đến 7.'},
                    {'id':'pdf-2','title':'fixture.txt','page':2,'source_version':'test','text':'Thở ra đến 8.'}]
    class Model:
        async def ainvoke(self,messages):
            return AIMessage(content=json.dumps({'supported':True,'answer':'Nín thở đến 7.',
                'citations':[{'id':source_id,'quote':quote_code}]}))
    engine=Agent(llm=Model(),rag=Rag(),web=FixtureWeb(),model_id='fixture:quote-code')
    with TestClient(create_app(engine,tmp_path/'trace.jsonl')) as client:
        result=client.post('/chatbot',json={'question':'Tai lieu','mode':'rag'}).json()
    assert result['status']==expected
    if expected=='ok':assert result['sources'][0]['quote']=='Nín thở đến 7.'

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
