"""Select a credential explicitly; export provenance booleans, never key material."""
import os
from pathlib import Path
from dotenv import dotenv_values

def configure_credentials(explicit_file, default_file):
    inherited=os.environ.get('GROQ_API_KEY')
    selected=Path(explicit_file).resolve() if explicit_file else Path(default_file).resolve()
    if explicit_file and not selected.is_file():
        raise FileNotFoundError('Explicit environment file does not exist')
    if selected.is_file():
        values=dotenv_values(selected,interpolate=False)
        key=values.get('GROQ_API_KEY') or ''
        if key:os.environ['GROQ_API_KEY']=key
        else:os.environ.pop('GROQ_API_KEY',None)
        # Preserve the already-selected model; this fix only overrides credentials.
        if values.get('GROQ_MODEL') and not os.getenv('GROQ_MODEL'):
            os.environ['GROQ_MODEL']=values['GROQ_MODEL']
        source='explicit_env_file' if explicit_file else 'project_env_file'
        os.environ['RAG_CHECK_KEY_FILE']=str(selected)
    else:
        key=inherited or '';source='inherited_environment'
        os.environ.pop('RAG_CHECK_KEY_FILE',None)
    os.environ['RAG_CHECK_KEY_SOURCE']=source
    return {'source':source,'selected_file':str(selected) if selected.is_file() else None,
            'inherited_key_present':bool(inherited),'selected_key_present':bool(key),
            'inherited_key_overridden':bool(inherited and selected.is_file() and inherited!=key),
            'process_matches_selected_file':os.environ.get('GROQ_API_KEY','')==key if selected.is_file() else None}

def sdk_credential_audit(engine):
    process_key=os.environ.get('GROQ_API_KEY') or ''
    configured=engine.llm.groq_api_key.get_secret_value()
    # Inspect the key actually stored by the async Groq SDK used for ainvoke.
    sdk_key=engine.llm.async_client._client.api_key
    path=os.environ.get('RAG_CHECK_KEY_FILE')
    file_key=(dotenv_values(path,interpolate=False).get('GROQ_API_KEY') or '') if path else None
    audit={'pid':os.getpid(),'source':os.getenv('RAG_CHECK_KEY_SOURCE','inherited_environment'),
           'selected_file':path,'process_key_present':bool(process_key),
           'model_id':engine.model_id,'langchain_key_matches_process':configured==process_key,
           'async_sdk_key_matches_process':sdk_key==process_key,
           'process_matches_selected_file':process_key==file_key if path else None}
    assert process_key and audit['langchain_key_matches_process'] and audit['async_sdk_key_matches_process']
    assert not path or audit['process_matches_selected_file']
    return audit
