"""Compare real local embeddings; answers are used only for span evaluation."""
import hashlib
import argparse
import json
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]/'CCNLTHD_LangGraph'
sys.path.insert(0, str(ROOT))
from faiss_retrieval import passages, load_embeddings, EMBEDDING_MODEL, EMBEDDING_REVISION
from pypdf import PdfReader


def norm(text):
    return re.sub(r'\s+', ' ', re.sub('[\uf0b7\u2022\u25cf]', ' ', text)).casefold().strip()


def main():
    import faiss
    import numpy as np
    parser=argparse.ArgumentParser()
    parser.add_argument('--segment',action='store_true')
    parser.add_argument('--section-context',action='store_true')
    parser.add_argument('--section-split',action='store_true')
    parser.add_argument('--strip-source-prefix',action='store_true')
    parser.add_argument('--label',default='faiss_retrieval_comparison')
    args=parser.parse_args()
    def prepare(text):
        if args.segment:
            from pyvi.ViTokenizer import tokenize
            text=tokenize(re.sub(r'\s+', ' ', text).strip())
        return text
    def question(text):
        if args.strip_source_prefix:
            text=re.sub(r'^Theo\s+Stress\.pdf\s*[,;:]?\s*','',text,flags=re.I)
        return prepare(text)
    output = Path(__file__).resolve().parent/args.label
    output.mkdir(exist_ok=False)
    cases_path = ROOT/'benchmarks/rag_check_cases.json'
    cases = json.loads(cases_path.read_text(encoding='utf-8'))['cases']
    pages = [(i+1, page.extract_text() or '') for i, page in enumerate(PdfReader(ROOT/'Stress.pdf').pages)]
    print('Loading pinned original model', flush=True)
    start = time.perf_counter()
    embeddings = load_embeddings()
    print('Encoding question vectors', flush=True)
    questions = np.asarray(embeddings.embed_documents([question(c['question']) for c in cases]), dtype='float32')
    all_summaries = []
    for size, overlap in [(500, 50), (650, 180), (1000, 180)]:
        if args.section_split:
            from retrieval import passages as section_passages
            chunks=section_passages(pages,size,overlap)
        else:
            chunks = passages(pages, size, overlap)
        print('Encoding', len(chunks), 'chunks', size, overlap, flush=True)
        vectors = np.asarray(embeddings.embed_documents([prepare((d.section+'\n' if args.section_context else '')+d.text) for d in chunks]), dtype='float32')
        for normalized in (False, True):
            doc_vectors, query_vectors = vectors.copy(), questions.copy()
            if normalized:
                faiss.normalize_L2(doc_vectors)
                faiss.normalize_L2(query_vectors)
            index = faiss.IndexFlatL2(vectors.shape[1])
            index.add(doc_vectors)
            distances, ids = index.search(query_vectors, 6)
            for k in (2, 3, 4, 6):
                label = f'chunk{size}_overlap{overlap}_k{k}_normalized{normalized}'
                rows = []
                for case, ds, indices in zip(cases, distances, ids):
                    docs = []
                    for rank, (distance, ordinal) in enumerate(zip(ds[:k], indices[:k]), 1):
                        doc = chunks[int(ordinal)]
                        assert pages[doc.page-1][1][doc.start:doc.end] == doc.text
                        docs.append({**doc.__dict__, 'rank': rank, 'score': float(distance), 'metric': 'squared_l2'})
                    coverage = [{'span': span, 'matching_ranks': [d['rank'] for d in docs if norm(span) in norm(d['text'])]}
                                for span in case['required_spans']]
                    rows.append({**case, 'documents': docs, 'span_coverage': coverage,
                                 'all_spans_present': all(c['matching_ranks'] for c in coverage) if case['answerable'] else None})
                groups = {}
                for group in dict.fromkeys(c['group'] for c in cases):
                    members = [r for r in rows if r['group'] == group]
                    groups[group] = {'n': len(members), 'all_spans_present': sum(r['all_spans_present'] is True for r in members)}
                summary = {'configuration': label, 'chunk_size': size, 'overlap': overlap, 'k': k,
                           'normalize_embeddings': normalized, 'chunk_count': len(chunks),
                           'embedding_model': EMBEDDING_MODEL, 'embedding_revision': EMBEDDING_REVISION,
                           'word_segmentation':'pyvi' if args.segment else None,
                           'embed_section_context':args.section_context,'strip_source_prefix':args.strip_source_prefix,
                           'chunk_policy':'section-page-windows' if args.section_split else 'recursive-character',
                           'dimensions': vectors.shape[1], 'index': 'IndexFlatL2', 'metric': 'squared_l2',
                           'groups': groups, 'all_spans_present': sum(r['all_spans_present'] is True for r in rows),
                           'failed_answerable_ids': [r['id'] for r in rows if r['all_spans_present'] is False],
                           'fixture': False, 'provider_calls': 0,
                           'scope': 'real embedding and FAISS; retrieval span coverage is not model answer correctness'}
                (output/(label+'.json')).write_text(json.dumps({'summary': summary, 'results': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
                all_summaries.append(summary)
                print(label, summary['all_spans_present'], '/25', summary['failed_answerable_ids'], flush=True)
    manifest = {'timestamp': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.perf_counter()-start,
                'pdf_sha256': hashlib.sha256((ROOT/'Stress.pdf').read_bytes()).hexdigest(),
                'cases_sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest(),
                'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('Rag_tool.py', 'faiss_retrieval.py')},
                'cases_are_regression_set': True, 'human_scores': None,
                'limitations': ['Question/reference set was created and inspected before this restoration; it is not an independent holdout.',
                                'Multiple configurations are compared on the same set; successful coverage is not independent quality validation.',
                                'No LLM is called in this run.'],
                'runs': all_summaries}
    (output/'summary.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
