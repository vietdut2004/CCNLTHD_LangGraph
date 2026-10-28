"""Single-attempt Tavily adapter; failures propagate to the API contract."""
import os
import httpx
from datetime import datetime,timezone

class SearchWebTool:
    name='search_web'
    async def search(self,query):
        key=os.getenv('TAVILY_API_KEY')
        if not key: raise RuntimeError('CONFIG_TAVILY_MISSING')
        async with httpx.AsyncClient(timeout=20,transport=httpx.AsyncHTTPTransport(retries=0)) as client:
            response=await client.post('https://api.tavily.com/search',
                json={'api_key':key,'query':query,'max_results':3,
                      'include_answer':False,'include_raw_content':False})
            response.raise_for_status()
            payload=response.json()
        if payload.get('error'): raise RuntimeError('WEB_PROVIDER_ERROR')
        return [{'id':f'web-{i+1}','title':row.get('title',''),
                 'url':row['url'],'text':row.get('content',''),
                 'retrieved_at':datetime.now(timezone.utc).isoformat()}
                for i,row in enumerate(payload.get('results',[]))
                if row.get('url','').startswith(('https://','http://')) and row.get('content')]
