"""Deterministic, source-only passage retrieval. No model/API or answer lookup.

Passages keep page offsets and section titles so a citation refers to the
original PDF text, not a reformatted answer. BM25 scores are lexical relevance,
not calibrated semantic confidence or proof that the source answers a question.
"""
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass,asdict

POLICY='section-balanced-bm25-v3'
MAX_CHARS=650
OVERLAP=180
DEFAULT_K=3
STOP=set('theo tai lieu pdf stress cua cac la va thi o duoc cho mot nhung nay do nao gi bao nhieu the nao'.split())

def normalize(text):
    text=''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if unicodedata.category(c)!='Mn')
    return text.replace('đ','d')

def tokens(text):
    return [t for t in re.findall(r'[a-z0-9]+',normalize(text)) if t not in STOP]

@dataclass(frozen=True)
class Passage:
    chunk_id:str
    page:int
    start:int
    end:int
    section:str
    text:str


def passages(pages,max_chars=MAX_CHARS,overlap=OVERLAP):
    """Split at section boundaries first, then create overlapping page windows."""
    if type(max_chars) is not int or max_chars<2:
        raise ValueError('max_chars must be an integer >= 2')
    if type(overlap) is not int or not 0<=overlap<max_chars:
        raise ValueError('overlap must be an integer in [0, max_chars)')
    out=[];section='';serial=0
    for page_num,text in pages:
        headings=list(re.finditer(r'^\d+(?:\.\d+)*\.\s+[^\n]+',text,re.M))
        boundaries=[0]+[m.start() for m in headings if m.start()>0]+[len(text)]
        for block_start,block_end in zip(boundaries,boundaries[1:]):
            hit=next((m for m in headings if m.start()==block_start),None)
            if hit:section=hit.group().strip()
            start=block_start
            while start<block_end:
                hard=min(block_end,start+max_chars)
                end=text.rfind('\n',start+max_chars//2,hard) if hard<block_end else hard
                if end<=start:end=hard
                content=text[start:end]
                if content.strip():
                    serial+=1;out.append(Passage(f'chunk-{serial:03d}',page_num,start,end,section,content))
                if end>=block_end:break
                target=max(start+1,end-overlap)
                line_start=text.rfind('\n',start+1,target)
                start=max(start+1,line_start+1 if line_start>=0 else target)
    return out

class BM25Index:
    def __init__(self,documents):
        self.documents=list(documents)
        self.counts=[Counter(tokens(d.section+' '+d.text)) for d in self.documents]
        self.lengths=[sum(c.values()) for c in self.counts]
        self.avg=sum(self.lengths)/max(1,len(self.lengths))
        self.df=Counter(t for c in self.counts for t in c)

    def search(self,query,k=DEFAULT_K):
        if type(k) is not int or k<1:
            raise ValueError('k must be a positive integer')
        query_tokens=sorted(set(tokens(query)));n=len(self.documents);ranked=[]
        query_phrase=' '.join(tokens(query))
        titles={re.sub(r'^\d+(?:\.\d+)*\.\s*','',d.section).strip() for d in self.documents if d.section}
        named=[title for title in titles if len(tokens(title))>=2 and ' '.join(tokens(title)) in query_phrase]
        # A comparative query may explicitly name several sections. Keep all of
        # them instead of silently dropping every section except the longest title.
        selected=sorted({' '.join(tokens(title)) for title in named})
        for i,(doc,c) in enumerate(zip(self.documents,self.counts)):
            if selected and not any(title in ' '.join(tokens(doc.section)) for title in selected):
                continue
            score=0.0
            for t in query_tokens:
                f=c[t]
                if not f:continue
                idf=math.log(1+(n-self.df[t]+.5)/(self.df[t]+.5))
                score+=idf*f*2.2/(f+1.2*(.25+.75*self.lengths[i]/(self.avg or 1)))
            # Exact multiword query phrases help distinguish named breathing exercises.
            q=normalize(query);section=normalize(doc.section)
            if section:
                title=re.sub(r'^\d+(?:\.\d+)*\.\s*','',section).strip()
                if len(title)>5 and title in q:score+=2.0
            if score>0:ranked.append((doc,score))
        ranked.sort(key=lambda x:(-x[1],x[0].page,x[0].start))
        if len(selected)>1:
            # Reserve one best passage per explicitly named section, within k.
            # Remaining slots retain BM25 order. Scores remain lexical scores;
            # the final order also reflects this section-coverage policy.
            best=[]
            for title in selected:
                hit=next((item for item in ranked if title in ' '.join(tokens(item[0].section))),None)
                if hit and all(hit[0].chunk_id!=item[0].chunk_id for item in best):best.append(hit)
            best.sort(key=lambda x:(-x[1],x[0].page,x[0].start))
            chosen=best[:k]
            ids={item[0].chunk_id for item in chosen}
            return (chosen+[item for item in ranked if item[0].chunk_id not in ids])[:k]
        return ranked[:k]
