"""Original Vietnamese embedding + FAISS retrieval, with source provenance."""
import hashlib
import os
from io import BytesIO
from pathlib import Path
from threading import Lock
from faiss_retrieval import (
    FAISSIndex, passages, load_embeddings, POLICY, MAX_CHARS, OVERLAP,
    DEFAULT_K, EMBEDDING_MODEL, EMBEDDING_REVISION, DEFAULT_CONFIG,
)

class RAGTOOL:
    name='rag_tool'
    def __init__(self,pdf_path=None,k=DEFAULT_K,max_chars=MAX_CHARS,overlap=OVERLAP,
                 normalize_embeddings=True,word_segmentation=True):
        if type(k) is not int or k<1:raise ValueError('k must be a positive integer')
        if type(max_chars) is not int or max_chars<2:
            raise ValueError('max_chars must be an integer >= 2')
        if type(overlap) is not int or not 0<=overlap<max_chars:
            raise ValueError('overlap must be an integer in [0, max_chars)')
        self.path=Path(pdf_path or os.getenv('RAG_PDF_PATH','Stress.pdf'))
        if not self.path.is_absolute():self.path=Path(__file__).resolve().parent/self.path
        self.k=k
        self.max_chars,self.overlap=max_chars,overlap
        self.embedding_model,self.embedding_revision=EMBEDDING_MODEL,EMBEDDING_REVISION
        self.normalize_embeddings,self.word_segmentation=normalize_embeddings,word_segmentation
        self.db,self.embeddings,self.loaded_version,self.lock=None,None,None,Lock()
    def configuration(self):
        return {**DEFAULT_CONFIG,'max_chars':self.max_chars,'overlap':self.overlap,'k':self.k,
                'embedding_model':self.embedding_model,'embedding_revision':self.embedding_revision,
                'normalize_embeddings':self.normalize_embeddings,'word_segmentation':'pyvi' if self.word_segmentation else None,
                'query_preprocessing':'strip-leading-source-pdf-preamble' if self.word_segmentation else None,
                }
    def version(self):
        return self._version(self.path.read_bytes())
    def _version(self,pdf_bytes):
        return (f'{hashlib.sha256(pdf_bytes).hexdigest()}:{POLICY}:'
                f'{self.embedding_model}@{self.embedding_revision}:'
                f'{self.max_chars}:{self.overlap}:{self.k}:'
                f'normalized={self.normalize_embeddings}:pyvi={self.word_segmentation}:mean')
    def retrieve(self,query):
        # Hash and parse the SAME byte snapshot, even if the PDF changes on disk.
        pdf_bytes=self.path.read_bytes()
        version=self._version(pdf_bytes)
        with self.lock:
            self._prepare_locked(pdf_bytes,version)
            hits=self.db.search(query,self.k)
        return [{'id':f'pdf-{i+1}','rank':i+1,'title':self.path.name,'page':doc.page,
                 'chunk_id':doc.chunk_id,'start':doc.start,'end':doc.end,
                 'section':doc.section,'source_version':version,'text':doc.text,
                 'score':float(score),'metric':'squared_l2'}
                for i,(doc,score) in enumerate(hits)]

    def _prepare_locked(self,pdf_bytes,version):
        if self.db is not None and self.loaded_version==version:
            return
        from pypdf import PdfReader
        pages=[(i+1,p.extract_text() or '') for i,p in enumerate(PdfReader(BytesIO(pdf_bytes)).pages)]
        chunks=passages(pages,self.max_chars,self.overlap)
        if chunks and self.embeddings is None:
            self.embeddings=load_embeddings(self.embedding_model,self.embedding_revision,
                normalize_embeddings=self.normalize_embeddings,word_segmentation=self.word_segmentation)
        self.db=FAISSIndex(chunks,self.embeddings)
        self.loaded_version=version

    def prepare(self):
        """Warm the real embedding/index before serving; never calls Groq."""
        pdf_bytes=self.path.read_bytes()
        version=self._version(pdf_bytes)
        with self.lock:
            self._prepare_locked(pdf_bytes,version)
            return {'source_version':version,'configuration':self.configuration(),
                    'chunk_count':len(self.db.documents),
                    'dimensions':self.db.store.index.d if self.db.store is not None else None}
