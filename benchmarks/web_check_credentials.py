"""Evaluation-only provenance; never logs credentials, prefixes or hashes."""
import os
from pathlib import Path
from dotenv import dotenv_values
from benchmarks.live_credentials import configure_credentials,sdk_credential_audit

def configure_web_credentials(explicit_file,default_file):
    groq=configure_credentials(explicit_file,default_file)
    selected=Path(explicit_file or default_file).resolve()
    inherited=os.getenv('TAVILY_API_KEY') or ''
    if selected.is_file():
        key=dotenv_values(selected,interpolate=False).get('TAVILY_API_KEY') or ''
        if key:os.environ['TAVILY_API_KEY']=key
        else:os.environ.pop('TAVILY_API_KEY',None)
        os.environ['WEB_CHECK_KEY_FILE']=str(selected)
    else:key=inherited;os.environ.pop('WEB_CHECK_KEY_FILE',None)
    return {'groq':groq,'tavily':{'selected_key_present':bool(key),'inherited_key_present':bool(inherited),
        'process_matches_selected_file':os.getenv('TAVILY_API_KEY','')==key if selected.is_file() else None,
        'source':'selected_file' if selected.is_file() else 'inherited_environment'}}

def audit_child(engine):
    groq=sdk_credential_audit(engine)
    path=os.getenv('WEB_CHECK_KEY_FILE');active=os.getenv('TAVILY_API_KEY') or ''
    selected=dotenv_values(path,interpolate=False).get('TAVILY_API_KEY') or '' if path else None
    assert active and (not path or selected==active)
    return {'groq':groq,'tavily':{'process_key_present':bool(active),'process_matches_selected_file':active==selected if path else None}}
