import os
from pathlib import Path
from threading import Lock
from typing import Optional

from dotenv import load_dotenv
from langchain_classic.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import ArgsSchema, BaseTool
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field, PrivateAttr, SecretStr

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CACHE_DIR = PROJECT_DIR / ".cache" / "huggingface"
os.environ.setdefault("HF_HOME", str(DEFAULT_CACHE_DIR))
os.environ.setdefault("HF_HUB_CACHE", str(DEFAULT_CACHE_DIR / "hub"))


class RAGInput(BaseModel):
    query: str = Field(..., description="Cau hoi can truy van trong tai lieu noi bo")


class RAGTOOL(BaseTool):
    name: str = "rag_tool"
    description: str = (
        "Dung de tra loi cau hoi ve tai lieu noi bo Stress.pdf, ky thuat hit tho, "
        "y nghia cua hit tho sau, va giam stress."
    )
    args_schema: ArgsSchema | None = RAGInput

    _pdf_path: Path = PrivateAttr()
    _k: int = PrivateAttr()
    _qa_chain: Optional[RetrievalQA] = PrivateAttr(default=None)
    _lock: Lock = PrivateAttr(default_factory=Lock)

    def __init__(self, pdf_path: str = "Stress.pdf", k: int = 2, **kwargs):
        super().__init__(**kwargs)
        self._pdf_path = Path(pdf_path)
        if not self._pdf_path.is_absolute():
            self._pdf_path = PROJECT_DIR / self._pdf_path
        self._k = k

    def _build_chain(self) -> RetrievalQA:
        if self._qa_chain is not None:
            return self._qa_chain

        with self._lock:
            if self._qa_chain is not None:
                return self._qa_chain

            if not self._pdf_path.exists():
                raise FileNotFoundError(f"Khong tim thay file tai lieu: {self._pdf_path}")

            loader = PyPDFLoader(str(self._pdf_path))
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_documents(docs)

            embedding_model = os.getenv(
                "EMBEDDING_MODEL",
                "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base",
            )
            embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
            vector_db = FAISS.from_documents(chunks, embeddings)
            retriever = vector_db.as_retriever(search_kwargs={"k": self._k})

            qa_prompt = PromptTemplate(
                input_variables=["question", "context"],
                template=(
                    "Ban la mot chuyen gia tam ly lam sang.\n"
                    "Chi su dung thong tin trong phan Tai lieu de tra loi. "
                    "Khong them kien thuc ben ngoai neu tai lieu khong neu.\n\n"
                    "=== Tai lieu ===\n{context}\n\n"
                    "=== Yeu cau ===\n"
                    "- Tra loi ngan gon, ro rang bang tieng Viet.\n"
                    "- Neu khong co thong tin, tra loi: 'Khong co thong tin trong tai lieu.'\n"
                    "- Neu noi dung co the anh huong suc khoe tam than, khuyen nguoi hoi tim chuyen gia.\n\n"
                    "Cau hoi: {question}\n\n"
                    "Cau tra loi:"
                ),
            )

            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("Missing GROQ_API_KEY in environment or .env file.")

            llm = ChatGroq(
                model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                temperature=0,
                api_key=SecretStr(groq_api_key),
            )

            self._qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": qa_prompt},
            )
            return self._qa_chain

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            result = self._build_chain().invoke({"query": query})
            return result.get("result", "Khong co cau tra loi tu RAG.")
        except Exception as exc:
            return f"RAGTOOL gap loi khi truy van tai lieu: {exc}"
