import csv,json,os
import pytest
from benchmarks.live_credentials import configure_credentials
from benchmarks.live_csv import token_columns,write_results_csv

def test_explicit_file_wins_over_stale_environment_without_logging_key(tmp_path,monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','stale-test-value')
    monkeypatch.delenv('RAG_CHECK_KEY_FILE',raising=False)
    path=tmp_path/'selected.env';path.write_text('GROQ_API_KEY=fresh-test-value\n')
    audit=configure_credentials(path,tmp_path/'unused.env')
    assert os.environ['GROQ_API_KEY']=='fresh-test-value'
    assert audit['inherited_key_overridden'] and audit['process_matches_selected_file']
    assert 'stale-test-value' not in json.dumps(audit) and 'fresh-test-value' not in json.dumps(audit)

def test_explicit_empty_key_does_not_fall_back_to_stale_key(tmp_path,monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','stale-test-value')
    path=tmp_path/'empty.env';path.write_text('GROQ_API_KEY=\n')
    audit=configure_credentials(path,tmp_path/'unused.env')
    assert not os.getenv('GROQ_API_KEY') and not audit['selected_key_present']

@pytest.mark.parametrize('usage',[
 {},
 {'usage_complete':False,'observed_tokens':{'input_tokens':0,'output_tokens':0,'total_tokens':0},'total_tokens':None},
 {'usage_complete':False,'observed_tokens':{'input_tokens':5,'output_tokens':2,'total_tokens':7},'total_tokens':None},
])
def test_unknown_usage_is_blank_in_exported_csv(tmp_path,usage):
    row={'id':'test','question':'q','reference':'r','http_status':502,'body':{'usage':usage},'started_at':'now','latency_ms':1}
    path=tmp_path/'results.csv';write_results_csv(path,[row])
    with path.open(encoding='utf-8-sig',newline='') as f:actual=next(csv.DictReader(f))
    assert all(actual[k]=='' for k in ('input_tokens','output_tokens','total_tokens'))

@pytest.mark.parametrize('values',[(0,0,0),(5,2,7)])
def test_complete_usage_preserves_known_zero_and_known_tokens(values):
    usage={'usage_complete':True,'total_tokens':values[2],
           'observed_tokens':dict(zip(('input_tokens','output_tokens','total_tokens'),values))}
    assert token_columns(usage)==values
