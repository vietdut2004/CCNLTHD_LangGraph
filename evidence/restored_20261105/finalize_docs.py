"""Finalize source documentation only after all 13 real RAG cases are recorded.

No provider/model/Word import or call. Without --execute this only validates and
prints a plan. Historical JSON objects are preserved unchanged by value.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


FINAL_GRAPH = "9df445c208d40dc57c00"
FINAL_UI_FOLDER = "live_conversation_2026-11-05T16-33-55-604Z"
FINAL_UI_TRACES = [
    "27807932154845fe8051681e33affcdb",
    "f1b58d16d65e4ccb90ff050ff8ea1b6c",
    "7738a52e3aa84b25882590fd6df1c2ba",
]
CASE_IDS = [*(f"rag_{i:02d}" for i in range(1, 9)), "new_01", "new_03", "new_06", "negative_01", "negative_02"]
PREFIX = "evidence/restored_20261105/"
VN_TIMEZONE = timezone(timedelta(hours=7))


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def usage_metrics(bodies: list[dict]) -> dict:
    keys = ("input_tokens", "output_tokens", "total_tokens")
    usages = [body.get("usage") or {} for body in bodies]
    observed = [usage.get("observed_tokens") or {} for usage in usages]
    complete = [usage.get("usage_complete") is True and all(isinstance(tokens.get(k), int) for k in keys)
                for usage, tokens in zip(usages, observed)]
    partial = {key: sum(tokens[key] for tokens in observed if isinstance(tokens.get(key), int))
               if any(isinstance(tokens.get(key), int) for tokens in observed) else None for key in keys}
    totals = {key: partial[key] if bodies and all(complete) else None for key in keys}
    calls = [usage.get("attempted_model_calls") for usage in usages]
    return {"requests": len(bodies), "usage_complete_requests": sum(complete), "usage_totals": totals,
            "observed_tokens": partial,
            "attempted_model_calls": sum(calls) if all(isinstance(n, int) for n in calls) else None,
            "missing_tokens_remain_null": True}


def latency_metrics(values: list[float]) -> dict:
    if not values or not all(isinstance(n, (int, float)) and math.isfinite(n) for n in values):
        raise ValueError("Missing or invalid latency; no replacement value will be invented.")
    ordered = sorted(values)
    return {"mean": round(sum(ordered) / len(ordered), 3),
            "p50": ordered[math.ceil(len(ordered) * .5) - 1],
            "p95": ordered[math.ceil(len(ordered) * .95) - 1],
            "percentile_method": "nearest-rank"}


def unit_metrics(path: Path) -> dict:
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    numbers = {name: sum(int(suite.attrib.get(name, 0)) for suite in suites)
               for name in ("tests", "skipped", "failures", "errors")}
    numbers["passed"] = numbers["tests"] - numbers["skipped"] - numbers["failures"] - numbers["errors"]
    numbers["seconds"] = round(sum(float(suite.attrib.get("time", 0)) for suite in suites), 3)
    if (numbers["passed"], numbers["skipped"], numbers["failures"], numbers["errors"]) != (67, 2, 0, 0):
        raise ValueError("Unit XML differs from the final 67 passed / 2 skipped run; review before finalizing.")
    return {**numbers, "junit_xml": PREFIX + path.name, "provider_calls": 0,
            "scope": "Unit/API mechanism checks; two skipped heavy cases are not passes and fixture results are not content quality."}


def source_quotes(body: dict, trace: dict) -> dict:
    documents = {}
    for event in trace.get("events", []):
        if event.get("kind") in ("retrieval_context", "web_context"):
            documents.update({doc.get("id"): doc for doc in event.get("documents", [])})
    sources = body.get("sources") or []
    checks = [{"id": source.get("id"), "page": source.get("page"),
               "quote_is_original_source_span": isinstance(source.get("quote"), str)
               and bool(source.get("quote"))
               and source["quote"] in documents.get(source.get("id"), {}).get("text", "")}
              for source in sources]
    events = [{"status": event.get("status"), "reason": event.get("reason")}
              for event in trace.get("events", []) if event.get("kind") == "evidence_check"]
    return {"source_entries": len(sources), "quote_checks": checks, "evidence_checks": events,
            "all_returned_quotes_match_original_spans": all(c["quote_is_original_source_span"] for c in checks) if checks else None,
            "semantic_entailment_or_answer_correctness": None}


def collect_attempts(ui: Path) -> list[dict]:
    attempts = []
    for folder in sorted(ui.glob("live_conversation_*")):
        if not folder.is_dir():
            continue
        records = load(folder / "requests_responses.json") if (folder / "requests_responses.json").exists() else []
        attempts.append({"path": PREFIX + "ui_restore/" + folder.name + "/",
                         "selected_final_ui_run": folder.name == FINAL_UI_FOLDER,
                         "recorded_requests": len(records),
                         "graph_ids": sorted({str((row.get("response") or {}).get("graph_id")) for row in records}),
                         "http_statuses": [row.get("http_status") for row in records],
                         "statuses": [(row.get("response") or {}).get("status") for row in records],
                         "trace_ids": [(row.get("response") or {}).get("trace_id") for row in records],
                         "capture_error_retained": (folder / "CAPTURE_ERROR.txt").exists(),
                         "stopped_live_retained": (folder / "STOPPED_LIVE.json").exists(),
                         "note": "Keep the whole recorded attempt; do not select answers across runs."})
    return attempts


def values_for_finalization(work: Path, repo: Path) -> dict:
    batch = work / "faiss_live_final_13"
    # This is the first gate: a running partial batch cannot update documentation.
    if not (batch / "summary.json").is_file():
        raise ValueError("Final 13-case summary is not present yet; no documentation changed.")
    summary = load(batch / "summary.json")
    rows = load(batch / "results.json")
    if summary.get("fixture") is not False or summary.get("n") != 13 or summary.get("planned") != 13 or len(rows) != 13:
        raise ValueError("Final RAG batch is incomplete or not real; no documentation changed.")
    if len({row.get("id") for row in rows}) != 13 or {row.get("id") for row in rows} != set(CASE_IDS):
        raise ValueError("Final RAG case IDs differ from old 8 + new_01/03/06 + two negatives.")
    manifest = load(repo / "docs/RESTORED_RUNTIME_IDENTITY.json")
    if manifest["identity"]["graph_id"] != FINAL_GRAPH:
        raise ValueError("Active source manifest differs from the selected final graph.")
    for filename, expected in {**manifest["identity"]["source_sha256"], **manifest["frontend_sha256"]}.items():
        if digest(repo / filename) != expected:
            raise ValueError(f"Active source changed after its identity was frozen: {filename}")
    for filename, expected in [("requirements-locked.txt", manifest["requirements_sha256"]), ("Stress.pdf", manifest["pdf_sha256"])]:
        if digest(repo / filename) != expected:
            raise ValueError(f"Locked file differs from manifest: {filename}")
    environment = load(batch / "environment.json")
    identity = load(batch / "identity.json")
    if identity["graph_id"] != FINAL_GRAPH or environment.get("graph_id") != FINAL_GRAPH or not environment.get("finished_at"):
        raise ValueError("Final batch has not finished with the expected identity.")
    if environment.get("concurrency") != 1 or environment.get("delay_seconds") != 45 or not environment.get("index_prepared_before_requests"):
        raise ValueError("Final batch does not match concurrency 1, 45-second delay, prepared FAISS.")
    per_case = []
    for row in rows:
        body, trace = row.get("body") or {}, row.get("trace") or {}
        if row.get("request", {}).get("mode") != "rag" or row["request"].get("use_cache") is not False:
            raise ValueError("Final RAG request is not explicit rag with cache disabled.")
        if set(row["request"]) - {"question", "mode", "use_cache"}:
            raise ValueError("Unexpected evaluator/reference fields in a final model request.")
        if body.get("graph_id") != FINAL_GRAPH or trace.get("graph_id") != FINAL_GRAPH or body.get("trace_id") != trace.get("trace_id"):
            raise ValueError("A final RAG response has no matching final-graph server trace.")
        if str(body.get("model_id", "")).startswith("fixture:") or body.get("model_id") != manifest["identity"]["model_id"]:
            raise ValueError("Final RAG result model differs from the configured real model.")
        per_case.append({"id": row["id"], "http_status": row.get("http_status"), "status": body.get("status"),
                         "code": body.get("code"), "route": body.get("route"), "trace_id": body.get("trace_id"),
                         "latency_ms": row.get("latency_ms"), "usage": body.get("usage") or {},
                         "answer_returned": body.get("status") == "ok",
                         "technical_completion": row.get("http_status") == 200 and body.get("status") in ("ok", "refused"),
                         "source_resolution": source_quotes(body, trace), "human_score": None, "semantic_correctness": None})
    calculated = {"n": len(rows), "planned": 13,
                  "technical_completed": sum(row["technical_completion"] for row in per_case),
                  "technical_errors": sum(not row["technical_completion"] for row in per_case),
                  "answers_returned": sum(row["answer_returned"] for row in per_case),
                  "refused": sum(row["status"] == "refused" for row in per_case),
                  "stopped_reason": summary.get("stopped_reason"), "latency_ms": latency_metrics([row["latency_ms"] for row in rows]),
                  **usage_metrics([row["body"] for row in rows])}
    for name in ("technical_completed", "technical_errors", "answers_returned", "refused", "usage_complete_requests", "usage_totals"):
        if summary.get(name) != calculated[name]:
            raise ValueError(f"Calculated final metric disagrees with raw summary: {name}")
    for name in ("mean", "p50", "p95"):
        if summary.get("latency_ms", {}).get(name) != calculated["latency_ms"][name]:
            raise ValueError(f"Calculated final latency disagrees with raw summary: {name}")
    ui_folder = work / "ui_restore" / FINAL_UI_FOLDER
    ui_rows = load(ui_folder / "requests_responses.json")
    if len(ui_rows) != 3 or [row.get("response", {}).get("trace_id") for row in ui_rows] != FINAL_UI_TRACES:
        raise ValueError("Selected final UI run/trace IDs differ; do not substitute answers from another run.")
    ui_bodies = [row["response"] for row in ui_rows]
    if [body.get("route") for body in ui_bodies] != ["rag", "answer", "web"] or any(row.get("http_status") != 200 or row["response"].get("status") != "ok" or row["response"].get("graph_id") != FINAL_GRAPH for row in ui_rows):
        raise ValueError("Selected final UI run does not contain the expected three real final-graph responses.")
    trace_map = {}
    for line in (repo / ".cache/request_traces.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            trace = json.loads(line)
            if trace.get("trace_id") in FINAL_UI_TRACES:
                trace_map[trace["trace_id"]] = trace
    if set(trace_map) != set(FINAL_UI_TRACES):
        raise ValueError("Selected UI traces are missing from the raw server log.")
    ui_cases = [{"question": row["request"]["question"], "http_status": row["http_status"], "status": row["response"]["status"],
                 "route": row["response"]["route"], "trace_id": row["response"]["trace_id"],
                 "latency_ms_browser": row["latency_ms_browser"], "usage": row["response"].get("usage") or {},
                 "source_resolution": source_quotes(row["response"], trace_map[row["response"]["trace_id"]]), "human_score": None}
                for row in ui_rows]
    retrieval = load(work / "faiss_final_production_retrieval/summary.json")
    baseline = load(work / "faiss_retrieval_comparison/chunk500_overlap50_k2_normalizedFalse.json")
    groups = retrieval["groups"]
    retrieval_counts = {"cases": sum(g["n"] for g in groups.values()), "answerable": sum(g["answerable"] for g in groups.values()),
                        "span_hits": sum(g["all_spans_hits"] for g in groups.values()),
                        "baseline_span_hits": baseline["summary"]["all_spans_present"],
                        "baseline_answerable": sum(row["answerable"] is True for row in baseline["results"])}
    if retrieval_counts != {"cases": 27, "answerable": 25, "span_hits": 25, "baseline_span_hits": 6, "baseline_answerable": 25}:
        raise ValueError("Retrieval comparison counts changed; review the documentation wording.")
    audits = [path.name for path in batch.glob("*audit*") if path.is_file()]
    content_audit = load(batch / "content_audit.json")
    if content_audit.get("human_grades_generated") is not False or len(content_audit.get("rows", [])) != 13:
        raise ValueError("Final source audit is missing, incomplete or not explicitly AI-only.")
    trace_by_id = {row["id"]: row["trace_id"] for row in per_case}
    if {row["id"] for row in content_audit["rows"]} != set(CASE_IDS) or any(row.get("trace_id") != trace_by_id.get(row["id"]) or row.get("human_score") is not None for row in content_audit["rows"]):
        raise ValueError("AI source audit does not match the same complete 13-case batch or contains human scores.")
    return {"manifest": manifest, "rag": calculated, "rag_cases": per_case, "rag_environment": environment,
            "ui": {"path": PREFIX + "ui_restore/" + FINAL_UI_FOLDER + "/", "cases": ui_cases,
                   "latency_ms_browser": latency_metrics([row["latency_ms_browser"] for row in ui_rows]),
                   **usage_metrics(ui_bodies)},
            "units": unit_metrics(work / "unit_tests_light_final.xml"), "retrieval": retrieval_counts,
            "attempts": collect_attempts(work / "ui_restore"), "audit_files": audits, "content_audit": content_audit,
            "final_graph": FINAL_GRAPH, "final_ui_folder": FINAL_UI_FOLDER}


def n(value) -> str:
    return "chưa có" if value is None else f"{value:,}".replace(",", ".")


def seconds(milliseconds) -> str:
    return "chưa có" if milliseconds is None else f"{milliseconds / 1000:.3f}".replace(".", ",") + " s"


def replace_paths(text: str) -> str:
    return text.replace("../phuc_hoi_theo_bao_cao_20261105/", PREFIX)


def known_limits(facts: dict) -> list[str]:
    by_id = {row["id"]: row for row in facts["rag_cases"]}
    limits = ["HTTP 200, trạng thái `ok` và quote khớp nguồn chỉ xác nhận một phần cơ chế; không đủ để chấm đáp án đúng.",
              "Bộ 27 câu retrieval đã dùng để sửa và chọn tham số. Kết quả 25/25 đủ span không phải đánh giá độc lập hoặc answer accuracy."]
    if by_id.get("rag_06", {}).get("status") == "refused":
        limits.append("`rag_06` vẫn từ chối dù retrieval có các span tham chiếu. Tìm được đoạn và tạo được câu trả lời là hai bước khác nhau.")
    incomplete = [row["id"] for row in facts["content_audit"]["rows"] if row.get("citation_assessment") in ("insufficient", "incomplete")]
    if incomplete:
        limits.append("Các câu " + ", ".join(f"`{case_id}`" for case_id in incomplete) + " có câu trả lời phù hợp tham chiếu nhưng quote chưa trực tiếp hoặc chưa đầy đủ cho ý được nêu. `rag_01` chỉ được audit là phần lớn có căn cứ, còn rút gọn bước giải thích và quote chưa trọn. Đây là đối chiếu của Codex, không phải điểm người thật.")
    limits.extend(["Không tự điền điểm người chấm cho lượt mới. RAG 96/104 và web 20/32 chỉ thuộc các phản hồi lịch sử đã được chấm.",
                   "Hai ca unit nặng bị bỏ qua trong lượt kiểm tra nhẹ do điều kiện tài nguyên. Không tính chúng là đạt; giữ log của các lần thiếu RAM.",
                   "FAISS/top-k mới có thể gửi ngữ cảnh dài hơn bản cũ. Không dùng latency hoặc token của BM25 để mô tả bản khôi phục."])
    return limits


def build_documents(work: Path, repo: Path, facts: dict) -> dict[Path, str]:
    docs = repo / "docs"
    source_lock = load(docs / "FINAL_SOURCE_LOCK.json")
    cleanup = load(docs / "CLEANUP_AND_PROVENANCE.json")
    historical_lock = source_lock["historical_submission_20261103"]
    historical_cleanup = cleanup["historical_cleanup_20261103"]
    before_history = canonical(historical_lock), canonical(historical_cleanup)
    manifest, rag, ui, units = facts["manifest"], facts["rag"], facts["ui"], facts["units"]
    active = source_lock["active_restoration_20261105"]
    active.update(status="real_final_runs_recorded_content_review_required", identity=manifest["identity"],
                  frontend_sha256=manifest["frontend_sha256"], final_commit=None,
                  requirements={"path": "requirements-locked.txt", "sha256": manifest["requirements_sha256"]},
                  final_live_validation={"status": "completed_technical_recording_not_human_quality_score", "graph_id": FINAL_GRAPH,
                                         "rag_batch": {"path": PREFIX + "faiss_live_final_13/", **rag, "per_case": facts["rag_cases"]},
                                         "ui_run": ui, "answer_accuracy": None, "human_scores": None})
    verification = source_lock["verification_20261105"]
    verification["unit_light"] = units
    verification["selected_final_ui_run"] = ui
    verification["earlier_live_attempts"] = [attempt for attempt in facts["attempts"] if not attempt["selected_final_ui_run"]]
    verification["final_rag_batch"] = {"path": PREFIX + "faiss_live_final_13/", **rag}
    verification["ai_source_audit"] = {"path": PREFIX + "faiss_live_final_13/content_audit.json",
        "method": facts["content_audit"]["method"], "scope": facts["content_audit"]["scope"],
        "human_grades_generated": False, "clinical_validation": False,
        "note": "Qualitative source comparison by Codex, not a human grade or independent accuracy estimate."}
    source_lock["updated_on"] = "2026-11-05"
    cleanup["active_restoration_20261105"].update(active_graph_id=FINAL_GRAPH,
        final_live_validation="recorded; technical/source checks separated from semantic correctness; no human score")
    cleanup.pop("new_evidence_workspace", None)
    cleanup["new_evidence_root"] = PREFIX.rstrip("/")
    cleanup["new_evidence_index"] = PREFIX + "INDEX_SHA256.json"
    cleanup["packaging_rule"] = "Curated source/results/traces with SHA index; no .env, keys, .venv, browser profiles or full report/draft plans in Git. Final report and its validation are handed over separately after commit."
    # Replace workspace-relative references without changing old historical objects.
    for key in list(source_lock):
        if key != "historical_submission_20261103":
            source_lock[key] = json.loads(replace_paths(json.dumps(source_lock[key], ensure_ascii=False)))
    for key in list(cleanup):
        if key != "historical_cleanup_20261103":
            cleanup[key] = json.loads(replace_paths(json.dumps(cleanup[key], ensure_ascii=False)))
    assert (canonical(source_lock["historical_submission_20261103"]), canonical(cleanup["historical_cleanup_20261103"])) == before_history

    journal = replace_paths((docs / "JOURNAL.md").read_text(encoding="utf-8"))
    journal_lines = []
    for line in journal.splitlines():
        if line.startswith("| 05/11/2026 — kiểm tra unit trong điều kiện thiếu RAM |"):
            line = f"| 05/11/2026 — kiểm tra unit trong điều kiện thiếu RAM | Lượt nhẹ cuối có {units['passed']} ca đạt, {units['skipped']} ca bỏ qua, không lỗi; không gọi provider. | `{PREFIX}unit_tests_light_final.xml`; tổng {units['tests']} ca, {units['seconds']:.3f} giây. Giữ các lần lỗi thiếu RAM; không tính ca bỏ qua là đạt. |"
        if line.startswith("| 05/11/2026 — hai lượt chat thật trong quá trình sửa |"):
            line = f"| 05/11/2026 — các lượt chat thật trong quá trình sửa | Giữ riêng {sum(not a['selected_final_ui_run'] for a in facts['attempts'])} thư mục thử trước lượt UI cuối, gồm từ chối và lỗi; mỗi lượt giữ đúng graph, response và usage của nó. | `{PREFIX}ui_restore/live_conversation_*/`; không ghép câu trả lời giữa các lượt. |"
        if line.startswith("| 05/11/2026 — trạng thái đang chốt |"):
            line = f"| 05/11/2026 — xác nhận bản khôi phục | Graph `{FINAL_GRAPH}` có một lượt UI ba câu riêng và một lượt RAG {rag['n']} câu đã ghi đủ. RAG hoàn tất kỹ thuật {rag['technical_completed']}/{rag['n']}, trả lời {rag['answers_returned']}, từ chối {rag['refused']}; chưa chấm đúng nội dung. | `{PREFIX}faiss_live_final_13/`, `{ui['path']}`. Không gộp hai lượt để tính latency/usage; không tự thêm điểm người chấm. |"
        journal_lines.append(line)
    journal = "\n".join(journal_lines).replace("Graph mới nhất khi cập nhật nhật ký là `2329a7abe36d6302844f`", f"Graph mới nhất khi cập nhật nhật ký là `{FINAL_GRAPH}`") + "\n"
    marker = "\n## Ghi nhận cuối sau lượt RAG đủ 13 câu\n"
    journal = journal.split(marker)[0] + marker + "\n" + f"Lượt UI được chọn giữ đúng ba trace `{FINAL_UI_TRACES[0]}`, `{FINAL_UI_TRACES[1]}` và `{FINAL_UI_TRACES[2]}`. Lượt RAG chạy tuần tự, cách nhau 45 giây; FAISS đã chuẩn bị trước, không có request warm-up của benchmark. Cả hai dùng model `{manifest['identity']['model_id']}`. Xem `CHECK_REPORT.md` để đọc kết quả theo từng câu và giới hạn, không dùng số HTTP hoàn tất thay cho độ đúng.\n"

    coverage_old = (docs / "COVERAGE_MATRIX.md").read_text(encoding="utf-8").split("\n## Kiểm tra bản khôi phục ngày 05/11/2026")[0]
    coverage_old = coverage_old.replace("Các kiểm tra ngày 05/11 được tách ở bảng tiếp theo.", "Các kiểm tra ngày 05/11 được tách ở bảng tiếp theo.")
    coverage = coverage_old + f"""

## Kiểm tra bản khôi phục ngày 05/11/2026

Minh chứng mới được tuyển chọn vào `{PREFIX}` và có `INDEX_SHA256.json`.
Các log lịch sử trong bảng trên giữ nguyên nguồn gốc. Runtime mới nhất dùng
graph `{FINAL_GRAPH}`; từng lượt trước vẫn giữ graph đã ghi khi chạy.

| Mảnh | Kết quả đã ghi | Minh chứng | Giới hạn |
|---|---|---|---|
| Source/lock/PDF | PhoBERT/PyVi + FAISS; chunk 1000, overlap 180, top-6; cùng checkpoint và PDF | `docs/RESTORED_RUNTIME_IDENTITY.json`, `docs/FINAL_SOURCE_LOCK.json`, `{PREFIX}EMBEDDING_AND_PDF_LOCK.json` | Runtime khác BM25; không gán số cũ sang bản mới |
| So sánh retrieval | Bản 500/50/top-2 không chuẩn hóa: 6/25 đủ span; cấu hình được chọn: 25/25 trên 27 câu, gồm 2 ngoài PDF | `{PREFIX}faiss_retrieval_comparison/`, `{PREFIX}faiss_final_production_retrieval/` | Embedding thật trong máy, không provider; đã dùng bộ câu để chọn tham số, không độc lập và không phải answer accuracy |
| Unit nhẹ | {units['passed']} đạt, {units['skipped']} bỏ qua, tổng {units['tests']}; {units['seconds']:.3f} giây, 0 lỗi | `{PREFIX}unit_tests_light_final.xml` | Không provider; fixture chỉ kiểm tra cơ chế; ca bỏ qua không tính đạt |
| Giao diện fixture | 12/12 ca Chrome về bố cục/session/error/render | `{PREFIX}ui_restore/ui_check_results.json` | Phản hồi gửi/nhận dùng fixture; ảnh initial chỉ có lời chào; 0 provider call |
| UI thật, một phiên ba câu | HTTP 200/ok cả ba; lần lượt RAG, hội thoại, web | `{ui['path']}` | Đúng một lượt được chọn, không ghép các lần thử; vẫn cần xem từng ý trả lời và nguồn |
| RAG thật, 13 câu | Hoàn tất kỹ thuật {rag['technical_completed']}/{rag['n']}; {rag['answers_returned']} trả lời, {rag['refused']} từ chối, {rag['technical_errors']} lỗi kỹ thuật | `{PREFIX}faiss_live_final_13/results.jsonl`, `summary.json`, `server_traces.jsonl` | 8 câu cũ + new_01/03/06 + 2 ngoài PDF; mode rag, cache tắt, concurrency 1, delay 45 giây, FAISS warm; không phải điểm nội dung |
| Các lần thử trước | {sum(not a['selected_final_ui_run'] for a in facts['attempts'])} thư mục UI trước lượt được chọn, giữ cả lỗi/từ chối | `{PREFIX}ui_restore/live_conversation_*/`, `{PREFIX}server_traces_all.jsonl` | Không thay định danh hoặc lấy câu tốt ở lượt khác ghép vào kết quả cuối |
| Quote/source | Model chọn mã quote; server đổi về đoạn nguồn nguyên bản và kiểm tra lại | `agent.py`, trace `evidence_check`, model outputs/context trong từng lượt | Quote khớp chưa chứng minh quote đủ hỗ trợ toàn bộ câu trả lời; chưa có điểm người thật mới |
| Đối chiếu nội dung bằng Codex | Audit đủ 13 câu cùng trace của một lượt, gồm cả từ chối chưa phù hợp và citation chưa đủ | `{PREFIX}faiss_live_final_13/content_audit.json`, `content_audit.csv` | AI audit, không điểm người thật, không xác nhận lâm sàng hoặc đánh giá độc lập |
| Lịch sử | Giữ nguyên 154 tệp và 9 snapshot runtime, RAG 96/104, web 20/32 | `handover/`, `{PREFIX}verify_historical_integrity.json` | Điểm chỉ thuộc các phản hồi lịch sử đã chấm |

Latency và usage của UI và RAG được tính riêng trong `CHECK_REPORT.md`; không
lấy tổng của hai lượt làm latency của một phiên. Các token thiếu usage để null
hoặc trống. Không suy ra đáp án đúng từ HTTP 200 hoặc trạng thái `ok`.

""" + "\n".join("- " + item for item in known_limits(facts)) + "\n"

    ui_table = []
    for i, case in enumerate(ui["cases"], 1):
        tokens = (case["usage"].get("observed_tokens") or {})
        ui_table.append(f"| {i} | {case['route']} | {seconds(case['latency_ms_browser'])} | {n(tokens.get('input_tokens'))} / {n(tokens.get('output_tokens'))} | `{case['trace_id']}` |")
    rag_table = []
    for case in facts["rag_cases"]:
        tokens = (case["usage"].get("observed_tokens") or {})
        rag_table.append(f"| {case['id']} | {case['http_status']} / {case['status']} | {seconds(case['latency_ms'])} | {n(tokens.get('input_tokens'))} / {n(tokens.get('output_tokens'))} | {case['source_resolution']['source_entries']} | `{case['trace_id']}` |")
    attempts = "\n".join(f"- `{attempt['path']}`: {attempt['recorded_requests']} request đã ghi; status `{', '.join(str(s) for s in attempt['statuses'])}`; " + ("lượt UI cuối được chọn." if attempt["selected_final_ui_run"] else "giữ riêng để đối chiếu quá trình sửa.") for attempt in facts["attempts"])
    limits = "\n".join("- " + item for item in known_limits(facts))
    audits = "\n".join(f"- `{PREFIX}faiss_live_final_13/{name}`" for name in facts["audit_files"]) or "Chưa có file audit riêng khi tạo tài liệu; không tự thay bằng điểm đúng/sai."
    content_labels = {"supported":"Có căn cứ đối chiếu", "mostly_supported":"Phần lớn có căn cứ", "incorrect_refusal":"Từ chối chưa phù hợp", "expected_refusal":"Từ chối phù hợp ngoài PDF"}
    citation_labels = {"direct":"Trực tiếp", "direct_with_noise":"Có quote trực tiếp, còn đoạn thừa", "insufficient":"Chưa đủ hỗ trợ ý trả lời", "incomplete":"Quote chưa trọn", "partial":"Một phần", "none":"Không có", "not_applicable":"Không áp dụng"}
    def cell(text):
        return str(text).replace("|", "\\|").replace("\n", " ")
    audit_table = "\n".join(f"| {row['id']} | {content_labels.get(row['content_assessment'],row['content_assessment'])} | {citation_labels.get(row['citation_assessment'],row['citation_assessment'])} | {cell(row['note'])} |" for row in facts["content_audit"]["rows"])
    check = f"""# Kiểm tra bản khôi phục theo báo cáo — 05/11/2026

Giao diện đã được đưa về bố cục trong ảnh báo cáo. RAG trở lại luồng PDF → chia
đoạn → embedding tiếng Việt → FAISS → trả lời theo nguồn. Số đo cũ vẫn thuộc
đúng source và lượt chạy của chúng; không đổi thành kết quả bản khôi phục.

## Source và những phần đã sửa

- Base Git trước sửa: `{manifest['base_commit']}`. Graph đã chạy các lượt cuối: `{FINAL_GRAPH}`. Commit xuất bản cuối xem release lock, không tự suy đoán tại đây.
- Model trả lời giữ `{manifest['identity']['model_id']}`. Checkpoint embedding `{manifest['identity']['retrieval_policy']['embedding_model']}` khóa revision `{manifest['identity']['retrieval_policy']['embedding_revision']}`; dùng PyVi, mean pooling, vector chuẩn hóa và FAISS IndexFlatL2. Khoảng cách nhỏ hơn là gần hơn, không phải xác suất đúng.
- PDF 6 trang giữ SHA-256 `{manifest['pdf_sha256']}`. Lock requirements hiện tại: `{manifest['requirements_sha256']}`. Source/asset hash nằm trong `docs/RESTORED_RUNTIME_IDENTITY.json`.
- Chunk 1000 ký tự, overlap 180, top-k 6 được chọn sau các lần so sánh. Bản 500/50/top-2 được chạy lại chỉ đủ span 6/25; bản được chọn đủ 25/25. Bộ 27 câu đã dùng để sửa/chọn tham số nên kết quả này không độc lập và không phải độ đúng của 25 đáp án model.
- Frontend khôi phục theo ảnh, logo lấy từ ảnh báo cáo. Chưa tìm thấy HTML gốc trong các nguồn đã kiểm tra; không nhận là sao chép nguyên source frontend cũ. Không hardcode câu trả lời lịch sử.
- Model dùng tool calling cho mode auto. Với câu trả lời dựa nguồn, model chọn mã quote; server giải mã về đoạn gốc, kiểm tra source ID và quote trước khi trả về. Có nguồn/quote khớp chưa thay thế đánh giá nội dung.

## Đã chạy gì

Unit nhẹ: **{units['passed']} đạt, {units['skipped']} bỏ qua**, tổng {units['tests']} ca, {units['seconds']:.3f} giây. Đây là kiểm tra cơ chế/unit/API, không gọi provider. Hai ca bỏ qua và các lần thiếu RAM được giữ đúng trạng thái. UI có 12/12 kiểm tra Chrome dùng fixture trình duyệt cho bước gửi/nhận, không dùng làm điểm model thật.

Retrieval production dùng embedding thật trong máy và FAISS, không fixture và không Groq/Tavily. Chi tiết chunk theo thứ hạng, trang, nội dung, điểm và reference ở `{PREFIX}faiss_final_production_retrieval/`. Giữ cả các cấu hình chưa đạt trong thư mục comparison.

## Cuộc trò chuyện thật, một phiên ba câu

Chỉ dùng lượt `{FINAL_UI_FOLDER}` với đúng ba trace bên dưới; không chọn câu trả lời từ các lần thử khác. Cả ba HTTP 200/status ok, lần lượt qua RAG, hội thoại và web. Đây là hoàn tất kỹ thuật, chưa phải ba điểm nội dung đạt.

| Câu | Nhánh | Latency trình duyệt | Input / output token | Trace |
|---|---|---:|---:|---|
{chr(10).join(ui_table)}

Tổng token của riêng lượt UI: input {n(ui['usage_totals']['input_tokens'])}, output {n(ui['usage_totals']['output_tokens'])}, tổng {n(ui['usage_totals']['total_tokens'])}; usage đầy đủ {ui['usage_complete_requests']}/{ui['requests']} request. Ảnh và raw response tại `{ui['path']}`.

## RAG thật, một lượt đủ 13 câu

Gồm 8 câu cũ, `new_01`, `new_03`, `new_06` và hai câu ngoài PDF. Các request đều
`mode:rag`, cache tắt; concurrency 1, delay 45 giây, index FAISS đã chuẩn bị
trước. Benchmark không gửi request warm-up; đây không phải phép đo cold-start.
Đáp án tham chiếu chỉ nằm ở bản ghi đánh giá, không gửi vào payload cho model.

Hoàn tất kỹ thuật **{rag['technical_completed']}/{rag['n']}**; có {rag['answers_returned']} phản hồi trả lời,
{rag['refused']} từ chối và {rag['technical_errors']} lỗi kỹ thuật. Latency của riêng lượt này:
mean {seconds(rag['latency_ms']['mean'])}, p50 {seconds(rag['latency_ms']['p50'])},
p95 {seconds(rag['latency_ms']['p95'])}, percentile nearest-rank. Tổng token:
input {n(rag['usage_totals']['input_tokens'])}, output {n(rag['usage_totals']['output_tokens'])},
tổng {n(rag['usage_totals']['total_tokens'])}; usage đầy đủ {rag['usage_complete_requests']}/{rag['n']}.

| ID | HTTP / trạng thái | Latency HTTP | Input / output token | Source entries | Trace |
|---|---|---:|---:|---:|---|
{chr(10).join(rag_table)}

Raw results, reference, context truy xuất, output model, trace và CSV nằm tại
`{PREFIX}faiss_live_final_13/`. Thiếu usage để null hoặc trống; không ghi 0 để thay
cho dữ liệu chưa có. Không cộng latency của lượt UI vào lượt RAG này.

## Nội dung còn cần đối chiếu

{limits}

Audit riêng nếu đã có:

{audits}

Đối chiếu dưới đây do Codex thực hiện trên toàn bộ response, tham chiếu và
context đã lưu của đúng lượt 13 câu. Không xem đây là điểm người thật, đánh giá
độc lập hoặc xác nhận lâm sàng:

| ID | Nội dung đối chiếu | Citation | Nhận xét |
|---|---|---|---|
{audit_table}

## Giữ các lần chưa đạt

{attempts}

Trace tổng của ngày chạy nằm tại `{PREFIX}server_traces_all.jsonl`, gồm cả live,
fixture, lỗi và từ chối theo đúng suite/graph của từng dòng. Không xóa lần thất
bại để chỉ giữ kết quả sau sửa. `TRACE_SELECTION.json` mô tả cách lọc ngày theo
giờ Việt Nam; `INDEX_SHA256.json` đối chiếu byte các tệp được tuyển chọn.

## Lệnh tái lập

Tạo môi trường bằng requirements khóa, tự cấu hình `.env` trên máy chạy; không
đưa `.env`, API key, `.venv`, hồ sơ Chromium hoặc cache model vào Git/gói nộp.
Không đổi model và không thêm dịch vụ trả phí. Cần đủ RAM cho checkpoint; chạy
API và kiểm tra embedding lần lượt để tránh nạp hai bản model cùng lúc.

```powershell
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe -m pip check
.\\.venv\\Scripts\\python.exe -m pytest tests -q
.\\.venv\\Scripts\\python.exe start_api.py
```

Khi `/health` báo index ready, mở terminal khác để chạy một bộ mới; đổi tên thư
mục output nếu đã có kết quả để giữ các lượt riêng biệt:

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 -m benchmarks.run_rag_live --base-url http://127.0.0.1:8000 --prepare-index --trace-file .cache/request_traces.jsonl --delay 45 --output ..\\rag_live_recheck_moi --ids {' '.join(CASE_IDS)}
node .\\{PREFIX.replace('/', chr(92))}ui_restore\\capture_live_conversation.cjs --run-live http://127.0.0.1:8000/
```

Kết quả trả lời thật cần API key/quota hợp lệ của dịch vụ hiện có. Nếu không
chạy được, giữ lỗi và dữ liệu còn thiếu; không dùng fixture hoặc đáp án tham
chiếu làm câu trả lời thật. Báo cáo Word/PDF cuối và hồ sơ chỉnh sửa văn bản được
bàn giao riêng sau khi khóa commit; không đưa bản nháp đầy đủ vào code Git.
"""
    return {docs / "FINAL_SOURCE_LOCK.json": json_text(source_lock), docs / "CLEANUP_AND_PROVENANCE.json": json_text(cleanup),
            docs / "JOURNAL.md": journal, docs / "COVERAGE_MATRIX.md": coverage, repo / "CHECK_REPORT.md": check}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Write the five docs only after all validation gates pass.")
    parser.add_argument("--work", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent / "CCNLTHD_LangGraph")
    args = parser.parse_args()
    work, repo = args.work.resolve(), args.repo.resolve()
    facts = values_for_finalization(work, repo)
    documents = build_documents(work, repo, facts)
    print(json.dumps({"ready": True, "mode": "execute" if args.execute else "read_only_plan", "graph_id": FINAL_GRAPH,
                      "rag_n": facts["rag"]["n"], "rag_statuses": dict(Counter(row["status"] for row in facts["rag_cases"])),
                      "ui_traces": FINAL_UI_TRACES, "unit_passed": facts["units"]["passed"], "unit_skipped": facts["units"]["skipped"],
                      "files": [path.relative_to(repo).as_posix() for path in documents], "provider_or_word_calls": 0}, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0
    stamp = datetime.now(VN_TIMEZONE).strftime("%Y%m%d_%H%M%S")
    backup = work / "docs_before_finalization" / stamp
    for path, text in documents.items():
        path.resolve().relative_to(repo)
        if path.exists():
            prior = backup / path.relative_to(repo)
            prior.parent.mkdir(parents=True, exist_ok=True)
            prior.write_bytes(path.read_bytes())
        path.write_text(text, encoding="utf-8")
    # Derived facts contain no model answer rewriting or human grades.
    (work / "finalized_docs_facts.json").write_text(json_text(facts), encoding="utf-8")
    print("Five documentation files updated. Historical JSON values retained; raw evidence untouched.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        print(f"Finalization blocked: {error}")
        raise SystemExit(1)
