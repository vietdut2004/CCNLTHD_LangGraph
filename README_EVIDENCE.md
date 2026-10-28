# Runtime contract for evidence v1.3

Base repository: https://github.com/vietdut2004/CCNLTHD_LangGraph
Base commit: 01ad2c014c2e948b8c6a97d875d2573ab2b2838b

Current runtime: evidence-v1.3-rag-check. README.md is the current handover status; handover/EVIDENCE_INDEX.json separates historical and current experiments. Source is integrated locally; remote push/merge and the group machine demo remain unverified.

## 1 Evidence identity

Every response and JSONL trace carries the same server-generated trace_id, graph_id, model_id and dependency versions. graph_id hashes the changed application source, model, prompt version and retry policy. Historical screenshots without these fields remain historical evidence: they cannot be retroactively assigned the new graph's identity. Trace files contain user questions and responses; use the curated public test cases before sharing them.

## 2 Tool executor

`python math_graph.py` invokes StructuredTool add/multiply in an actual compiled StateGraph. It writes `.cache/math_traces.json` with names, arguments, results, final output and two expected failure cases. It does not use an LLM or validate Groq tool-selection accuracy. Original OutputParserException screenshots must remain labeled failed historical trials.

## 3 Fixed experiments

Create a fresh virtual environment, then:

```powershell
python -m pip install -r requirements-evidence.txt
python -m pytest -q tests/test_evidence.py
python -m benchmarks.run_evidence --fixture --output evidence_fixture
```

Fixture adapters make no external HTTP, model or embedding calls. Fixture token usage is missing for a simulated model call, not zero; calls that provably never invoked a model are zero. Fixture timings must never be copied into the Groq/RAG/web performance table.

For current BM25 RAG, install `requirements-locked.txt` (FAISS requirements-rag-extra.txt is historical), supply a reviewed Stress.pdf via RAG_PDF_PATH, and configure GROQ_API_KEY and TAVILY_API_KEY locally. Never include a real .env in a shared package. Start the new API in a separate port so the baseline can be retained:

```powershell
python -m pip freeze > environment_live.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8001
# In another terminal using the same venv and repository:
python -m benchmarks.run_evidence --base-url http://127.0.0.1:8001 --server-traces .cache/request_traces.jsonl --output evidence_live --repeat 1
```

There are 18 fixed cases plus one excluded warm-up per run. Repetitions 1..3 are allowed, up to 55 requests. No client retry is configured; calls may incur provider costs on the live system. Each repetition uses fresh demo-user namespaces while preserving the explicit memory and cache pairs within that repetition. Use one server worker: RAM checkpoints and RAM cache are not shared across workers/process restarts.

The benchmark separately records technical_error, observable_case_pass, semantic_quality=null, timestamps, latency, usage coverage, sources and matched server trace. Missing telemetry fails the observable check. It exports manual_grading.csv; a reviewer grades factual support, relevance, scope and source accuracy 0..2 each and records their name. Verify expected RAG answers against the actual reviewed PDF before interpreting any content score. A source ID or matching quote is necessary evidence, not proof that the answer follows semantically from it.

## 4 Error and retry contract

POST /chatbot retains the response text field and adds status, code, trace_id, graph_id, model_id, route, sources and usage. HTTP 200 has status=ok or refused. 422=INVALID_REQUEST; 429=UPSTREAM_QUOTA; 502=UPSTREAM_AUTH or UPSTREAM_OR_GRAPH_ERROR; 503=missing configuration/source/session capacity/graph step limit; 504=UPSTREAM_TIMEOUT. Error bodies never expose raw exception messages. Retrying is explicitly zero at the Groq SDK, Tavily HTTP transport, tool, graph and benchmark-client layers. Model timeout=25s; web timeout=20s; whole API deadline=60s; recursion_limit=12; max output=1536 tokens/call. Sync PDF/model-loading threads may continue after a deadline cancellation; process isolation is needed for hard CPU-job cancellation.

## 5 Cache and sessions

The old FAISS example is similarity retrieval, not a complete semantic answer cache. The new AnswerCache is an **exact normalized-question cache**, only for RAG, opt-in, TTL 300s, capacity 128; it is disabled for anonymous and session requests. Keys include demo user, source-content hash, retrieval/chunk configuration, model and prompt version. It stores the supported answer and returned source quotes. The PDF index is rebuilt when its source version changes. Similar but different wording/negation misses; user and source changes miss. This is not semantic-hit accuracy or a calibrated similarity threshold experiment.

Session requests must supply user_id and session_id. Hashing the pair namespaces an InMemorySaver. Only node answer sends up to two prior human/AI exchanges; grounded currently uses the current question and retrieved sources; a different user/session starts fresh. Requests within a session are serialized; 128 session namespaces maximum per process. Persistence is RAM only. Caller-supplied user_id is a demonstration namespace, NOT authentication or production authorization; add authenticated identity before multi-user deployment. MySQL long-term memory is still a planned extension.

## 6 Sources, refusal and scope

The explicit keyword router sends requests to rag, web or answer; diagnosis/prescription keywords go to refuse. RAG/web invoke one retrieval tool and then a grounded generation node. Empty sources, malformed grounding JSON, unknown citation IDs or quotes absent from the returned source lead to refusal. The router and keyword scope check are limited demo policies, not a clinical safety classifier. Content returns PDF page/version or web URL and an actual source quote. The graph contains no multi-agent expansion. Do not claim clinical effectiveness, diagnostic ability, real-web reliability or semantic correctness from fixture tests.
