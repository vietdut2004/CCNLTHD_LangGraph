"""Derived CSV: unknown/incomplete usage remains empty; known zero stays zero."""
import csv

def token_columns(usage):
    if usage.get('usage_complete') is not True:
        return None,None,None
    observed=usage.get('observed_tokens',{})
    values=tuple(observed.get(k) for k in ('input_tokens','output_tokens','total_tokens'))
    if not all(type(v) is int and v>=0 for v in values) or values[0]+values[1]!=values[2]:
        return None,None,None
    if usage.get('total_tokens')!=values[2]:return None,None,None
    return values

def write_results_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['id','question','reference','http','status','trace_id','model','timestamp','latency_ms',
                         'input_tokens','output_tokens','total_tokens','usage_complete'])
        for r in rows:
            b=r['body'];usage=b.get('usage',{});values=token_columns(usage)
            writer.writerow([r['id'],r['question'],r['reference'],r['http_status'],b.get('status'),b.get('trace_id'),
                             b.get('model_id'),r['started_at'],r['latency_ms'],*values,usage.get('usage_complete')])
