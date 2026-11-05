"""Verify final evidence links and raw/derived consistency offline, with stdlib."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))


def checked_path(relative):
    path = (ROOT / relative).resolve()
    assert path.is_relative_to(ROOT), 'Evidence path escapes repository'
    assert path.is_file(), 'Missing evidence: ' + relative
    return path


def verify():
    expected = load('handover/EXPECTED_RUNTIME_IDENTITY.json')
    restored_path = ROOT/'docs/RESTORED_RUNTIME_IDENTITY.json'
    restored = load('docs/RESTORED_RUNTIME_IDENTITY.json') if restored_path.is_file() else None
    historical_root = restored['historical_runtime_snapshot'] if restored else ''
    for name, digest in expected['source_sha256'].items():
        relative = historical_root+'/'+name if historical_root else name
        assert hashlib.sha256(checked_path(relative).read_bytes()).hexdigest() == digest, relative
    if restored:
        for name, digest in {**restored['identity']['source_sha256'],**restored['frontend_sha256']}.items():
            assert hashlib.sha256(checked_path(name).read_bytes()).hexdigest() == digest, name
        assert hashlib.sha256(checked_path('requirements-locked.txt').read_bytes()).hexdigest() == restored['requirements_sha256']
    evidence_hashes = load('handover/EVIDENCE_SHA256.json')
    for name, digest in evidence_hashes.items():
        assert hashlib.sha256(checked_path('handover/' + name).read_bytes()).hexdigest() == digest, name
    assert checked_path('requirements.txt').read_text(encoding='utf-8').splitlines()[-1] == '-r requirements-locked.txt'
    assert hashlib.sha256(checked_path('Stress.pdf').read_bytes()).hexdigest() == '91c16764898a88f26bb73706d1188afd3e3631f8a462c08fd76130a64ebc736a'
    rows = load('evidence/indexes/PER_CASE_RESULTS.json')
    assert len(rows) == 41
    with checked_path('evidence/indexes/PER_CASE_RESULTS.csv').open(encoding='utf-8-sig', newline='') as stream:
        flat = list(csv.DictReader(stream))
    assert len(flat) == len(rows)
    for row, line in zip(rows, flat):
        result = json.loads(checked_path(row['raw_results']).read_text(encoding='utf-8-sig'))[row['raw_result_index_0_based']]
        assert result['body']['trace_id'] == row['trace_id'] == line['trace_id']
        assert result['body']['response'] == row['response']
        assert result['body']['status'] == row['status']
        trace_ids = {json.loads(t)['trace_id'] for t in checked_path(row['trace_file']).read_text(encoding='utf-8-sig').splitlines() if t.strip()}
        assert row['trace_id'] in trace_ids
        if row['context_file']:
            checked_path(row['context_file'])
        if row['human_scores_link']:
            checked_path(row['human_scores_link'])
        for key in ['input_tokens', 'output_tokens', 'total_tokens']:
            assert line[key] == ('' if row[key] is None else str(row[key]))
            if not row['usage_complete']:
                assert row[key] is None
    for dataset in load('evidence/indexes/QUESTION_ANSWER_DATASETS.json'):
        assert hashlib.sha256(checked_path(dataset['path']).read_bytes()).hexdigest() == dataset['sha256']
    retrieval = load('evidence/indexes/RETRIEVAL_COVERAGE_PER_CASE.json')
    assert len(retrieval) == 27
    assert sum(r['answerable'] and r['spans_covered'] for r in retrieval) == 25
    assert len([r for r in rows if r['method'] == 'live_failed_auth' and r['http_status'] == 502]) == 2
    for folder, total, count in [('human_rag_13', 96, 13), ('human_web_4', 20, 4)]:
        name = 'CHAM_NGUOI_THAT.json' if count == 13 else 'CHAM_WEB_NGUOI_THAT.json'
        grades = load('handover/evidence/' + folder + '/' + name)
        assert len(grades['rows']) == count and sum(r['total'] for r in grades['rows']) == total
    return {'verified': True, 'historical_runtime_files': len(expected['source_sha256']),
            'active_graph_id':restored['identity']['graph_id'] if restored else expected['graph_id'],
            'historical_graph_id':expected['graph_id'],
            'preserved_evidence_files': len(evidence_hashes), 'indexed_http_results': len(rows),
            'retrieval_cases': 27, 'answerable_span_hits': 25,
            'real_auth_failure_runs_preserved': 2, 'human_scores_unchanged': True,
            'provider_calls': 0, 'semantic_scores_generated': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
