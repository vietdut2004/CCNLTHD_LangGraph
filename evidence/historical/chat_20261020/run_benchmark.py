r"""Run real sequential HTTP requests and export a shareable evidence bundle.

Usage: .\.venv\Scripts\python.exe benchmarks\run_benchmark.py
The existing demo on port 8000 is kept running. An instrumented instance of
the same main.app runs on port 8001 for this measurement only.
"""
import csv
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import socket
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

PROJECT = Path(__file__).resolve().parents[1]
LOCAL_TZ = timezone(timedelta(hours=7))
STAMP = datetime.now(LOCAL_TZ).strftime("%Y%m%d_%H%M%S")
OUT = PROJECT.parent / "ket_qua_kiem_thu" / STAMP
OUT.mkdir(parents=True, exist_ok=False)
PROBE = "http://127.0.0.1:8001"
BASELINE = "http://127.0.0.1:8000"
FALLBACK = "Xin loi, da xay ra loi khi xu ly hoi thoai. Vui long thu lai."


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def percentile(values, fraction):
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def aggregate(rows):
    latency = [r["client_latency_ms"] for r in rows]
    successes = [r["client_latency_ms"] for r in rows if r["passed"]]
    calls = [c for r in rows for c in r.get("model_calls", [])]
    usage = [c["usage_metadata"] for c in calls if c.get("usage_metadata")]
    return {
        "requests": len(rows), "passed": sum(r["passed"] for r in rows),
        "failed": sum(not r["passed"] for r in rows),
        "failure_rate_pct": round(100 * sum(not r["passed"] for r in rows) / len(rows), 3) if rows else None,
        "http_4xx_5xx": sum(r.get("http_status", 0) >= 400 for r in rows),
        "transport_errors": sum(bool(r.get("transport_error")) for r in rows),
        "application_fallbacks": sum(r.get("application_fallback", False) for r in rows),
        "requests_with_tool_error": sum(r.get("tool_error", False) for r in rows),
        "latency_ms": {"mean": round(sum(latency) / len(latency), 3), "p50": percentile(latency, .5), "p95": percentile(latency, .95), "min": min(latency), "max": max(latency)} if latency else {},
        "successful_latency_ms": {"mean": round(sum(successes) / len(successes), 3), "p50": percentile(successes, .5), "p95": percentile(successes, .95)} if successes else {},
        "completed_model_calls": len(calls), "calls_with_usage_metadata": len(usage),
        "observed_tokens": {key: sum(u.get(key, 0) for u in usage) for key in ("input_tokens", "output_tokens", "total_tokens")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-tools", action="store_true", help="Include RAG/web only after authorizing external document/tool requests.")
    args = parser.parse_args()
    # Refuse to attach results to another process already listening on the probe port.
    with socket.socket() as check:
        if check.connect_ex(("127.0.0.1", 8001)) == 0:
            raise RuntimeError("Port 8001 is already in use; no process was stopped.")
    started = datetime.now(LOCAL_TZ)
    client = httpx.Client(timeout=10, trust_env=False)
    schema_response = client.get(BASELINE + "/openapi.json")
    schema_response.raise_for_status()
    schema = schema_response.json()
    dump("openapi.json", schema)
    baseline_docs_status = client.get(BASELINE + "/docs").status_code
    env_settings = dotenv_values(PROJECT / ".env")
    effective = {**env_settings, **os.environ}
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT, text=True).strip()
    source_names = ["main.py", "agent.py", "Rag_tool.py", "searchweb_tool.py", "requirements.txt"]
    environment = {
        "started_at": started.isoformat(), "timezone": "Asia/Ho_Chi_Minh (UTC+07:00)",
        "baseline_url": BASELINE, "measured_url": PROBE,
        "baseline_docs_http_status": baseline_docs_status,
        "git_revision": revision,
        "source_sha256": {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() for name in source_names},
        "python": platform.python_version(), "platform": platform.platform(), "cpu": platform.processor(), "logical_cpu_count": os.cpu_count(),
        "packages": {p: importlib.metadata.version(p) for p in ("fastapi", "uvicorn", "langchain", "langchain-core", "langchain-groq", "langgraph", "sentence-transformers", "torch", "httpx")},
        "model": effective.get("GROQ_MODEL") or "openai/gpt-oss-20b", "temperature": 0,
        "groq_key_present": bool(effective.get("GROQ_API_KEY")), "tavily_key_present": bool(effective.get("TAVILY_API_KEY")),
        "concurrency": 1, "warmup_requests": 1, "delay_between_requests_seconds": 2,
        "request_timeout_seconds": 120, "retries_by_benchmark": 0,
        "tool_tests_enabled": args.include_tools,
        "planned_requests_including_warmup": 17 if args.include_tools else 14,
        "notes": ["Same main.app imported by benchmarks.probe_api; callbacks and middleware only; original demo remains on 8000.", "Latency is client-observed full HTTP response time, not time to first token.", "Input tokens include system prompt and tool schemas; output tokens use provider-reported usage including reasoning where reported.", "Completed model calls without provider usage are missing data, not zero; failed requests can have unreported token consumption.", "No claims about concurrent load, clinical quality, or production reliability are made."]
    }
    dump("environment.json", environment)
    env = dict(os.environ, BENCHMARK_METRICS_PATH=str(OUT / "server_metrics.jsonl"), BENCHMARK_ALLOW_TOOLS="1" if args.include_tools else "0", PYTHONIOENCODING="utf-8")
    server_log = (PROJECT / ".cache" / "benchmark_server.log")
    server_log.parent.mkdir(exist_ok=True)
    log = server_log.open("w", encoding="utf-8")
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "benchmarks.probe_api:app", "--host", "127.0.0.1", "--port", "8001", "--log-level", "warning"], cwd=PROJECT, env=env, stdout=log, stderr=log, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    rows = []
    try:
        for _ in range(60):
            if process.poll() is not None:
                raise RuntimeError("Measurement server exited; inspect .cache/benchmark_server.log locally.")
            try:
                if client.get(PROBE + "/openapi.json").status_code == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Measurement server did not become ready.")
        instrumented_schema = client.get(PROBE + "/openapi.json").json()
        dump("openapi_measured.json", instrumented_schema)
        environment["schema_equal_between_instances"] = schema == instrumented_schema
        if not environment["schema_equal_between_instances"]:
            raise RuntimeError("Schema changed between instances; stopping benchmark.")
        tests = [
            ("warmup", "warmup", {"question": "Xin chào. Chỉ chào lại một câu ngắn, không dùng công cụ."}, 200),
            *[(f"basic_{i:02d}", "basic", {"question": question}, 200) for i, question in enumerate([
                "Xin chào. Chỉ chào lại một câu ngắn, không dùng công cụ.",
                "Hãy tính 12 cộng 8. Trả lời ngắn, không dùng công cụ.",
                "Dịch 'Have a nice day' sang tiếng Việt, không dùng công cụ.",
                "Viết một lời cảm ơn người bạn đã giúp tôi làm bài, không dùng công cụ.",
                "Gợi ý cách chia một bài tập lớn thành ba bước nhỏ, không dùng công cụ.",
                "Cho tôi một lời động viên trước buổi thuyết trình, không dùng công cụ.",
                "Kể tên ba màu cơ bản. Trả lời ngắn, không dùng công cụ.",
                "Viết một câu chúc ngủ ngon nhẹ nhàng, không dùng công cụ.",
                "Giải thích sự khác nhau giữa mục tiêu và kế hoạch bằng hai câu, không dùng công cụ.",
                "Gợi ý một cách sắp xếp bàn học gọn gàng, không dùng công cụ.",
            ], 1)],
            ("invalid_missing", "validation", {}, 422),
            ("invalid_type", "validation", {"question": ["xin chào"]}, 422),
            ("invalid_null", "validation", {"question": None}, 422),
            ("web_01", "web", {"question": "Hãy dùng search_web tìm tin tức công nghệ mới nhất hôm nay và nêu nguồn."}, 200),
            ("rag_cold_01", "rag", {"question": "Hãy dùng rag_tool: tài liệu Stress.pdf nói gì về lợi ích của hít thở sâu?"}, 200),
            ("rag_repeat_02", "rag", {"question": "Hãy dùng rag_tool: tài liệu Stress.pdf nói gì về lợi ích của hít thở sâu?"}, 200),
        ]
        if not args.include_tools:
            tests = [test for test in tests if test[1] not in ("web", "rag")]
        dump("test_cases.json", [{"id": ident, "category": category, "body": body, "expected_status": status} for ident, category, body, status in tests])
        timed_out = False
        for ident, category, body, expected in tests:
            if timed_out:
                break
            print(f"Running {ident}...", flush=True)
            before = time.perf_counter()
            row = {"request_id": ident, "category": category, "request_body": body, "expected_status": expected, "started_at": datetime.now(LOCAL_TZ).isoformat()}
            try:
                response = client.post(PROBE + "/chatbot", json=body, headers={"X-Benchmark-ID": ident}, timeout=120)
                row.update(http_status=response.status_code, response_body=response.json())
                row["application_fallback"] = row["response_body"].get("response") == FALLBACK
            except (httpx.HTTPError, ValueError) as exc:
                row["transport_error"] = type(exc).__name__
                timed_out = isinstance(exc, httpx.TimeoutException)
            row["client_latency_ms"] = round((time.perf_counter() - before) * 1000, 3)
            rows.append(row)
            with (OUT / "http_results.jsonl").open("a", encoding="utf-8") as output:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"  {row.get('http_status', row.get('transport_error'))}; {row['client_latency_ms']} ms", flush=True)
            time.sleep(2)
    finally:
        # Stop only the measurement process and its download/worker children.
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        log.close()
        client.close()
    records = {}
    metrics_file = OUT / "server_metrics.jsonl"
    if metrics_file.exists():
        for line in metrics_file.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            records[record["request_id"]] = record
    for row in rows:
        record = records.get(row["request_id"], {})
        row.update({k: record.get(k, [] if k != "server_latency_ms" else None) for k in ("model_calls", "tool_calls", "errors", "server_latency_ms")})
        row["metrics_record_present"] = bool(record)
        row["tool_error"] = any(t.get("reported_error") for t in row["tool_calls"]) or any(e["kind"] == "tool" for e in row["errors"])
        required_tool = {"web": "search_web", "rag": "rag_tool"}.get(row["category"])
        row["required_tool_invoked"] = any(t.get("name") == required_tool for t in row["tool_calls"]) if required_tool else None
        row["passed"] = row.get("http_status") == row["expected_status"] and not row.get("application_fallback") and not row.get("transport_error") and not row["errors"] and not row["tool_error"] and (not required_tool or row["required_tool_invoked"])
        if row["category"] != "validation":
            row["passed"] = row["passed"] and bool(row.get("response_body", {}).get("response", "").strip())
    dump("results.json", rows)
    groups = {category: aggregate([r for r in rows if r["category"] == category]) for category in ("basic", "validation", "web", "rag") if any(r["category"] == category for r in rows)}
    workload = [r for r in rows if r["category"] not in ("validation", "warmup")]
    summary = {"groups": groups, "valid_workload": aggregate(workload), "planned_requests_including_warmup": len(tests), "executed_requests_including_warmup": len(rows), "warmup_excluded_from_summary": True, "percentile_method": "nearest rank ceil(p * n)", "failure_definition": "Expected HTTP status mismatch, transport error, application fallback, observed LLM/tool error, empty answer, or requested tool not invoked. 422 on deliberately invalid input is a passing validation test.", "quality_scoring": "No semantic/clinical quality score; pass means observable technical completion only."}
    dump("summary.json", summary)
    environment["finished_at"] = datetime.now(LOCAL_TZ).isoformat()
    environment["source_sha256_after"] = {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() for name in source_names}
    environment["source_unchanged_during_run"] = environment["source_sha256"] == environment["source_sha256_after"]
    dump("environment.json", environment)
    fields = ["request_id", "category", "http_status", "expected_status", "client_latency_ms", "server_latency_ms", "passed", "application_fallback", "tool_error", "input_tokens", "output_tokens", "total_tokens", "completed_model_calls", "calls_with_usage_metadata", "transport_error"]
    with (OUT / "results.csv").open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            record = {k: row.get(k) for k in fields}
            usage = [c["usage_metadata"] for c in row["model_calls"] if c.get("usage_metadata")]
            for key in ("input_tokens", "output_tokens", "total_tokens"):
                record[key] = sum(u.get(key, 0) for u in usage) if usage else None
            record["completed_model_calls"] = len(row["model_calls"])
            record["calls_with_usage_metadata"] = len(usage)
            writer.writerow(record)
    report(summary, rows, environment)
    for name in ("run_benchmark.py", "probe_api.py"):
        (OUT / name).write_bytes((PROJECT / "benchmarks" / name).read_bytes())
    # Only curated artifacts are exported; never .env, project logs or git data.
    archive = OUT.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(OUT.iterdir()):
            if path.is_file():
                bundle.write(path, arcname=path.name)
    print(json.dumps({"output_dir": str(OUT), "zip": str(archive), "summary": summary}, ensure_ascii=False), flush=True)


def report(summary, rows, environment):
    lines = [
        "# Kết quả kiểm thử thực tế API demo — dữ liệu cho Chương 13", "",
        f"Thời điểm: {environment['started_at']} đến {environment['finished_at']} (UTC+7).",
        f"Mã nguồn: `{environment['git_revision']}`. Model: `{environment['model']}`, temperature = 0.",
        "",
        "## Cách đo", "",
        "Schema được lấy trực tiếp từ `http://127.0.0.1:8000/openapi.json`. Bản demo `/docs` trả HTTP 200. Các phép đo có token chạy qua HTTP ở `http://127.0.0.1:8001/chatbot`, là cùng `main.app` được thêm callback và middleware trong tiến trình riêng; không sửa mã nghiệp vụ. Schema hai bản được so sánh bằng nhau. Bản ở cổng 8000 được giữ nguyên.",
        "",
        "Đo tuần tự (concurrency = 1), một warm-up không tính vào bảng, nghỉ 2 giây giữa các yêu cầu, timeout mỗi yêu cầu 120 giây, công cụ đo không retry. SDK có thể tự retry theo cấu hình mặc định của demo. Latency dùng `perf_counter`, tính từ trước khi gửi POST tới khi nhận toàn bộ phản hồi; bao gồm HTTP, callback, LLM, công cụ và retry nếu có. Không phải time-to-first-token. P50/P95 dùng nearest-rank; mẫu nhỏ nên P95 chỉ mang tính mô tả lần chạy này.",
        "",
        "Token lấy từ `AIMessage.usage_metadata` do Groq/LangChain cung cấp cho từng lời gọi model hoàn tất; có giữ thêm token_usage gốc trong log. Cộng tất cả lời gọi, kể cả lời gọi lồng trong RAG nếu được callback ghi nhận. Output token có thể bao gồm reasoning token theo cách tính của nhà cung cấp. Đây không phải phép đếm từ ký tự. Không quy đổi thành chi phí. Lời gọi lỗi không có usage là dữ liệu thiếu; không suy ra tiêu thụ bằng 0.",
        "",
        "## Kết quả", "",
        "| Nhóm | Số yêu cầu | Đạt / lỗi | Tỷ lệ lỗi kỹ thuật | Trung bình (ms) | P50 (ms) | P95 (ms) | Input / output / tổng token quan sát |", 
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {"basic": "Hội thoại cơ bản", "validation": "Đầu vào sai có chủ đích", "web": "Tìm kiếm web", "rag": "RAG tài liệu"}
    for category, group in summary["groups"].items():
        latency = group["latency_ms"]
        tokens = group["observed_tokens"]
        token_text = f"{tokens['input_tokens']} / {tokens['output_tokens']} / {tokens['total_tokens']}" if group['calls_with_usage_metadata'] else "Không có usage được ghi nhận"
        lines.append(f"| {labels[category]} | {group['requests']} | {group['passed']} / {group['failed']} | {group['failure_rate_pct']}% | {latency['mean']} | {latency['p50']} | {latency['p95']} | {token_text} |")
    group = summary["valid_workload"]
    lines += ["", f"Tổng workload đầu vào hợp lệ, không gồm warm-up và kiểm thử validation: **{group['requests']} yêu cầu**, **{group['failed']} lỗi kỹ thuật ({group['failure_rate_pct']}%)**. Mean = {group['latency_ms'].get('mean')} ms; P50 = {group['latency_ms'].get('p50')} ms; P95 = {group['latency_ms'].get('p95')} ms. Các con số tổng hợp gồm cả yêu cầu lỗi; xem `successful_latency_ms` trong summary.json để tách latency thành công.", "", "## Phân loại lỗi và giới hạn", "", "- HTTP 422 cho payload sai có chủ đích là kiểm tra validation đạt, không đưa vào mẫu số lỗi workload hợp lệ.", "- HTTP 200 chưa đủ để tính là thành công: demo bắt exception và trả câu xin lỗi với mã 200; công cụ cũng có thể trả chuỗi lỗi cho model.", "- Một yêu cầu bị tính lỗi khi sai mã HTTP mong đợi, lỗi truyền tải, trả fallback, callback thấy lỗi model/công cụ, trả câu rỗng, hoặc không gọi công cụ được yêu cầu. Model có thể che lỗi công cụ bằng câu trả lời bình thường; log công cụ vẫn dùng để đánh dấu lỗi.", "- Không đánh giá chất lượng nội dung, độ chính xác RAG hay hiệu quả lâm sàng. Bộ mẫu nhỏ, chạy một lần, không kiểm thử tải đồng thời và không đại diện SLA production.", f"- Khóa Tavily có cấu hình lúc đo: **{'Có' if environment['tavily_key_present'] else 'Không'}**. Không xuất giá trị khóa.", f"- Đã chạy {len(rows)}/{summary['planned_requests_including_warmup']} yêu cầu dự kiến (gồm warm-up). Nếu timeout làm dừng đo, các ca chưa chạy không được điền số liệu.", ""]
    if not environment['tool_tests_enabled']:
        lines += ["- Lần đo này chỉ gồm hội thoại và validation. Công cụ bị chặn trước khi thực thi; không gửi nội dung Stress.pdf hoặc truy vấn tìm kiếm ra ngoài. Chưa có số liệu RAG/web; không suy rộng kết quả này cho hai chức năng đó.", ""]
    for row in rows:
        if not row['passed']:
            details = []
            if row.get('transport_error'):
                details.append(row['transport_error'])
            if row.get('application_fallback'):
                details.append('API trả fallback')
            for error in row.get('errors', []):
                details.append(f"{error['kind']}: {error['type']}: {error['message'][:500]}")
            for tool in row.get('tool_calls', []):
                if tool.get('reported_error'):
                    details.append(f"{tool.get('name')}: {tool.get('output_excerpt', '')[:600]}")
            if row.get('required_tool_invoked') is False:
                details.append('không gọi công cụ được yêu cầu')
            lines.append(f"- `{row['request_id']}`: " + ('; '.join(details) or 'Không đạt tiêu chí kỹ thuật') + '.')
    lines += ["", "## Tệp để gửi ChatGPT", "", "Gửi `openapi.json`, `BAO_CAO_KIEM_THU.md`, `summary.json`, `results.csv` và `results.json`. `http_results.jsonl` là phản hồi HTTP gốc; `server_metrics.jsonl` là usage/công cụ/lỗi theo request_id. `environment.json` ghi phiên bản và SHA-256 mã nguồn. Hai script đi kèm cho phép chạy lại trong thư mục `benchmarks` của project đã cài dependencies. Không có `.env` hay khóa API trong gói xuất.", "", "Có thể yêu cầu ChatGPT: 'Dựa trên các tệp đính kèm, bổ sung Chương 13 với phương pháp đo, bảng latency/token/error, phân biệt validation và lỗi công cụ, nêu giới hạn mẫu nhỏ. Chỉ dùng số liệu log; không tự suy ra token cho lời gọi lỗi hoặc tuyên bố chất lượng lâm sàng.'", ""]
    (OUT / "BAO_CAO_KIEM_THU.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
