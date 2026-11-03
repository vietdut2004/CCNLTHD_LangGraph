"""Measurement overlay for the unchanged main.app; no credentials in output."""
import contextvars
import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

import main
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers.context import register_configure_hook

app = main.app
CURRENT = contextvars.ContextVar("demo_benchmark_callback", default=None)
register_configure_hook(CURRENT, inheritable=True)


def redact(value):
    text = str(value)
    for name, secret in os.environ.items():
        if secret and len(secret) >= 8 and any(s in name.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            text = text.replace(secret, "[REDACTED]")
    return re.sub(r"gsk_[A-Za-z0-9]+", "[REDACTED]", text)


class Recorder(BaseCallbackHandler):
    raise_error = True

    def __init__(self):
        self.models = []
        self.tools = []
        self.errors = []
        self.lock = threading.Lock()

    def on_llm_end(self, response, **kwargs):
        message = response.generations[0][0].message
        metadata = message.response_metadata or {}
        usage = message.usage_metadata
        with self.lock:
            self.models.append({
                "run_id": str(kwargs.get("run_id")),
                "model": metadata.get("model_name"),
                "usage_metadata": usage,
                "provider_token_usage": metadata.get("token_usage") or (response.llm_output or {}).get("token_usage"),
                "finish_reason": metadata.get("finish_reason"),
            })

    def on_llm_error(self, error, **kwargs):
        with self.lock:
            self.errors.append({"kind": "llm", "type": type(error).__name__, "message": redact(error)[:1000]})

    def on_tool_start(self, serialized, input_str, **kwargs):
        if os.environ.get("BENCHMARK_ALLOW_TOOLS") != "1":
            raise PermissionError("External tool execution is disabled for this measurement suite.")
        with self.lock:
            self.tools.append({"run_id": str(kwargs.get("run_id")), "name": (serialized or {}).get("name"), "input": redact(input_str)[:1000], "started_at": time.perf_counter()})

    def on_tool_end(self, output, **kwargs):
        text = redact(getattr(output, "content", output))
        with self.lock:
            for tool in self.tools:
                if tool["run_id"] == str(kwargs.get("run_id")):
                    tool["latency_ms"] = round((time.perf_counter() - tool.pop("started_at")) * 1000, 3)
                    tool["output_excerpt"] = text[:1500]
                    tool["reported_error"] = any(marker in text for marker in ("Loi khi tim kiem:", "RAGTOOL gap loi", "Missing TAVILY_API_KEY"))

    def on_tool_error(self, error, **kwargs):
        with self.lock:
            self.errors.append({"kind": "tool", "type": type(error).__name__, "message": redact(error)[:1000]})


@app.middleware("http")
async def measure(request, call_next):
    if request.url.path != "/chatbot":
        return await call_next(request)
    recorder = Recorder()
    token = CURRENT.set(recorder)
    started = time.perf_counter()
    record = {
        "request_id": request.headers.get("X-Benchmark-ID"),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
    }
    try:
        response = await call_next(request)
        record["http_status"] = response.status_code
        return response
    except Exception as exc:
        recorder.errors.append({"kind": "http", "type": type(exc).__name__, "message": redact(exc)[:1000]})
        raise
    finally:
        CURRENT.reset(token)
        record.update(server_latency_ms=round((time.perf_counter() - started) * 1000, 3), model_calls=recorder.models, tool_calls=recorder.tools, errors=recorder.errors)
        # Remove internal timing values from tools interrupted by an exception.
        for tool in record["tool_calls"]:
            tool.pop("started_at", None)
        path = Path(os.environ["BENCHMARK_METRICS_PATH"])
        with path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
