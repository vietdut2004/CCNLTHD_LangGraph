"""PDF chunks and semantic search used by the restored original RAG demo.

The legacy BM25 implementation remains in retrieval.py for reproducing its
historical results. It is not a fallback for this retriever.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import re

POLICY = 'phobert-pyvi-faiss-normalized-l2-v1'
MAX_CHARS = 1000
OVERLAP = 180
DEFAULT_K = 6
EMBEDDING_MODEL = 'VoVanPhuc/sup-SimCSE-VietNamese-phobert-base'
EMBEDDING_REVISION = '608779b86741a8acd8c8d38132974ff04086b138'
ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = {
    'name': POLICY, 'max_chars': MAX_CHARS, 'overlap': OVERLAP, 'k': DEFAULT_K,
    'embedding_model': EMBEDDING_MODEL, 'embedding_revision': EMBEDDING_REVISION,
    'embedding_device': 'cpu', 'normalize_embeddings': True, 'pooling': 'mean',
    'word_segmentation': 'pyvi', 'query_preprocessing': 'strip-leading-source-pdf-preamble',
    'max_input_tokens': 256, 'index_type': 'IndexFlatL2', 'metric': 'squared_l2',
    'score_direction': 'smaller_is_nearer',
}


@dataclass(frozen=True)
class Passage:
    chunk_id: str
    page: int
    start: int
    end: int
    section: str
    text: str


def passages(pages, max_chars=MAX_CHARS, overlap=OVERLAP):
    """Use the original recursive 500/50 splitter and retain PDF offsets."""
    if type(max_chars) is not int or max_chars < 2:
        raise ValueError('max_chars must be an integer >= 2')
    if type(overlap) is not int or not 0 <= overlap < max_chars:
        raise ValueError('overlap must be an integer in [0, max_chars)')
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars, chunk_overlap=overlap, add_start_index=True)
    result = []
    section = ''
    for page_number, text in pages:
        headings = list(re.finditer(r'^\d+(?:\.\d+)*\.\s+[^\n]+', text, re.M))
        for doc in splitter.create_documents([text]):
            start = doc.metadata['start_index']
            end = start + len(doc.page_content)
            if start < 0 or text[start:end] != doc.page_content:
                raise ValueError('PDF chunk offsets do not match source text')
            preceding = [h for h in headings if h.start() <= start]
            if preceding:
                section = preceding[-1].group().strip()
            result.append(Passage(f'chunk-{len(result)+1:03d}', page_number,
                                  start, end, section, doc.page_content))
        if headings:
            section = headings[-1].group().strip()
    return result


def load_embeddings(model_name=EMBEDDING_MODEL, revision=EMBEDDING_REVISION,
                    normalize_embeddings=False, word_segmentation=False):
    """Prefer the pinned local snapshot; download that same revision if absent."""
    from langchain_huggingface import HuggingFaceEmbeddings
    cache = Path(os.getenv('HF_HUB_CACHE',
                 str(Path(os.getenv('HF_HOME', str(ROOT/'.cache'/'huggingface')))/'hub')))
    snapshot = cache/('models--'+model_name.replace('/', '--'))/'snapshots'/revision
    local = (snapshot/'config.json').is_file() and (
        (snapshot/'model.safetensors').is_file() or (snapshot/'pytorch_model.bin').is_file())
    model_kwargs = {'device': 'cpu', 'local_files_only': local}
    if not local:
        model_kwargs['revision'] = revision
    base = HuggingFaceEmbeddings(
        model_name=str(snapshot.resolve()) if local else model_name,
        cache_folder=str(cache), model_kwargs=model_kwargs,
        encode_kwargs={'normalize_embeddings': normalize_embeddings}, show_progress=False)
    if not word_segmentation:
        return base
    from langchain_core.embeddings import Embeddings
    from pyvi.ViTokenizer import tokenize

    class VietnameseEmbeddings(Embeddings):
        @staticmethod
        def prepare(text):
            return tokenize(re.sub(r'\s+', ' ', text).strip())

        def embed_documents(self, texts):
            return base.embed_documents([self.prepare(text) for text in texts])

        def embed_query(self, text):
            # Remove the source preamble, not the substantive question. This is
            # generic PDF syntax; no answers or question IDs enter retrieval.
            text = re.sub(r'^Theo\s+(?:tài liệu\s+)?[^\s,;:]+\.pdf\s*[,;:]?\s*',
                          '', text, flags=re.I)
            return base.embed_query(self.prepare(text))
    return VietnameseEmbeddings()


class FAISSIndex:
    """IndexFlatL2: smaller squared Euclidean distance means nearer vectors."""
    def __init__(self, documents, embeddings):
        from langchain_community.vectorstores import FAISS
        self.documents = list(documents)
        self.store = None
        if self.documents:
            self.store = FAISS.from_texts(
                [doc.text for doc in self.documents], embeddings,
                metadatas=[{'ordinal': i} for i in range(len(self.documents))])

    def search(self, query, k=DEFAULT_K):
        if type(k) is not int or k < 1:
            raise ValueError('k must be a positive integer')
        if self.store is None:
            return []
        return [(self.documents[doc.metadata['ordinal']], float(distance))
                for doc, distance in self.store.similarity_search_with_score(query, k=k)]
