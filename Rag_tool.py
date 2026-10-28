"""Versioned PDF passages, BM25 by default; no nested LLM call."""
import hashlib
import os
from io import BytesIO
from pathlib import Path
from threading import Lock
from retrieval import BM25Index,passages,POLICY,MAX_CHARS,OVERLAP,DEFAULT_K

class RAGTOOL:
    name='rag_tool'
    def __init__(self,pdf_path=None,k=DEFAULT_K,max_chars=MAX_CHARS,overlap=OVERLAP):
        if type(k) is not int or k<1:raise ValueError('k must be a positive integer')
        passages([],max_chars,overlap)  # Validate window parameters before use.
        self.path=Path(pdf_path or os.getenv('RAG_PDF_PATH','Stress.pdf'))
        if not self.path.is_absolute():self.path=Path(__file__).resolve().parent/self.path
        self.k=k
        self.max_chars,self.overlap=max_chars,overlap
        self.db,self.loaded_version,self.lock=None,None,Lock()
    def version(self):
        return self._version(self.path.read_bytes())
    def _version(self,pdf_bytes):
        return f'{hashlib.sha256(pdf_bytes).hexdigest()}:{POLICY}:{self.max_chars}:{self.overlap}:{self.k}'
    def retrieve(self,query):
        # Hash and parse the SAME byte snapshot, even if the PDF changes on disk.
        pdf_bytes=self.path.read_bytes()
        version=self._version(pdf_bytes)
        with self.lock:
            if self.db is None or self.loaded_version!=version:
                from pypdf import PdfReader
                pages=[(i+1,p.extract_text() or '') for i,p in enumerate(PdfReader(BytesIO(pdf_bytes)).pages)]
                self.db=BM25Index(passages(pages,self.max_chars,self.overlap))
                self.loaded_version=version
            hits=self.db.search(query,self.k)
        return [{'id':f'pdf-{i+1}','rank':i+1,'title':self.path.name,'page':doc.page,
                 'chunk_id':doc.chunk_id,'start':doc.start,'end':doc.end,
                 'section':doc.section,'source_version':version,'text':doc.text,
                 'score':float(score),'metric':'bm25_lexical'}
                for i,(doc,score) in enumerate(hits)]
