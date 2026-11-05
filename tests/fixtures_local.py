"""Deterministic adapters; no provider/network/embedding call is made."""
import json
from langchain_core.messages import AIMessage

class FixtureModel:
    def __init__(self,missing_usage=False,bad_citation=False):
        self.calls=0
        self.missing_usage=missing_usage
        self.bad_citation=bad_citation
        self.contexts=[]
    def bind_tools(self,tools,**kwargs):
        return FixtureToolSelection(self)
    async def ainvoke(self,messages):
        self.calls+=1
        self.contexts.append(messages)
        system=messages[0].content
        if 'Trả duy nhất JSON' in system:
            docs=json.loads(system.split('\n',1)[1])
            doc=docs[0]
            content=json.dumps({'supported':True,'answer':'Tra loi dua tren nguon thu nghiem.',
                'citations':[{'id':'fake-source' if self.bad_citation else doc['id'],
                              'quote':doc['quotes'][0]['code']}]},ensure_ascii=False)
        else:
            contents=[m.content if hasattr(m,'content') else m[1] for m in messages]
            content='Da doc '+str(len(contents)-1)+' tin nhan. '+contents[-1]
        # Deliberately absent usage: never fabricate provider token counts for fixtures.
        return AIMessage(content=content)

class FixtureToolSelection:
    """Simulate named model tool calls only; this is not production routing."""
    def __init__(self,model):self.model=model
    async def ainvoke(self,messages):
        self.model.calls+=1
        self.model.contexts.append(messages)
        value=messages[-1].content if hasattr(messages[-1],'content') else messages[-1][1]
        lowered=value.casefold()
        name=('rag_tool' if any(s in lowered for s in ('stress.pdf','tai lieu','hit tho'))
              else 'search_web' if any(s in lowered for s in ('tim kiem','phim','web')) else None)
        if name:
            return AIMessage(content='',tool_calls=[{'name':name,'args':{'query':value},'id':'fixture-call','type':'tool_call'}])
        return AIMessage(content='Phan hoi gia lap; khong phai model that.')

class FixtureRag:
    def __init__(self,empty=False,fail=False):
        self.calls=0
        self.revision='fixture-source-v1'
        self.empty,self.fail=empty,fail
    def version(self): return self.revision
    def retrieve(self,query):
        self.calls+=1
        if self.fail: raise FileNotFoundError('fixture missing file')
        if self.empty: return []
        return [{'id':'pdf-1','title':'fixture.txt','page':1,'source_version':self.revision,
                 'text':'Day la du lieu gia lap kiem tra luong; khong phai tai lieu y khoa.'}]

class FixtureWeb:
    async def search(self,query):
        return [{'id':'web-1','title':'Fixture only','url':'https://example.invalid/fixture',
                 'text':'Day la ket qua web gia lap; khong co truy van Internet thuc te.'}]
