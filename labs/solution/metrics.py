import time

def observe(call, case_id, group="baseline"):
    start = time.perf_counter()
    try:
        result = call()
        status, error = "ok", None
    except Exception as exc:
        result = {}
        status, error = "error", type(exc).__name__
    elapsed = (time.perf_counter() - start) * 1000
    usage = result.get("usage") or {}
    row = {
        "case_id": case_id, "group": group,
        "latency_ms": round(elapsed, 3),
        "status": status, "error_type": error,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    return result, row
