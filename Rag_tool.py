"""Local PDF retrieval. No nested model call or text-form error fallback."""
import hashlib
import os
from pathlib import Path
from threading import Lock

class RAGTOOL:
    name = 'rag_tool'
    def __init__(self, pdf_path=None, k=2):
        self.path = Path(pdf_path or os.getenv('RAG_PDF_PATH','Stress.pdf'))
        if not self.path.is_absolute(): self.path=Path(__file__).resolve().parent/self.path
        self.k=k
        self.embedding_model=os.getenv('EMBEDDING_MODEL','VoVanPhuc/sup-SimCSE-VietNamese-phobert-base')
        self.db, self.loaded_version, self.lock = None, None, Lock()

    def version(self):
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        return f'{digest}:{self.embedding_model}:500:50:{self.k}'

    def retrieve(self, query):
        version=self.version()
        with self.lock:
            if self.db is None or self.loaded_version!=version:
                from langchain_community.document_loaders import PyPDFLoader
                from langchain_community.vectorstores import FAISS
                from langchain_huggingface import HuggingFaceEmbeddings
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                docs=PyPDFLoader(str(self.path)).load()
                chunks=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50).split_documents(docs)
                if not chunks: return []
                embeddings=HuggingFaceEmbeddings(model_name=self.embedding_model)
                self.db=FAISS.from_documents(chunks,embeddings)
                self.loaded_version=version
            hits=self.db.similarity_search_with_score(query,k=self.k)
        return [{'id':f'pdf-{i+1}','title':self.path.name,
                 'page':int(doc.metadata.get('page',0))+1,'source_version':version,
                 'text':doc.page_content,'score':float(score),'metric':'squared_l2'}
                for i,(doc,score) in enumerate(hits)]
