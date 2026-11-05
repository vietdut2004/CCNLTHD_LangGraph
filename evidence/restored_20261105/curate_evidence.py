"""Select restoration evidence without loading a model or opening Word.

The default is a read-only plan. Use --execute after all final runs have finished.
Source artifacts are copied byte-for-byte. The consolidated trace file is a
derived selection of original JSONL lines, with no response rewriting.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import zipfile


WORKSPACE_NAME = "phuc_hoi_theo_bao_cao_20261105"
EXPECTED_FINAL_GRAPH = "9df445c208d40dc57c00"
VN_TIMEZONE = timezone(timedelta(hours=7))
EVIDENCE_DATE = date(2026, 11, 5)

# Prefixes name evidence categories, not a general recursive workspace copy.
DIRECTORY_PREFIXES = (
    "faiss_retrieval_comparison", "faiss_segmented_comparison",
    "faiss_sectioned_comparison", "faiss_pooling_comparison",
    "faiss_production_retrieval", "faiss_final_production_retrieval",
    "faiss_production_source_snapshot", "faiss_live", "runtime_snapshots",
)
TOP_LEVEL_PATTERNS = (
    "EMBEDDING*_LOCK.json", "EMBEDDING_TOKEN_LENGTH_AUDIT.json",
    "faiss*.log", "faiss*_identity.json", "faiss_live*", "*tests*.xml",
    "unit*.log", "pytest*.log", "diagnostic_*.json", "ui_attempt_*_server_traces.jsonl",
    "runtime_before_*.json", "verify_historical_integrity.json", "verify_restored_strict*.json",
    "pull_before_continue.json", "source_before_78b118f.zip", "RAG_RESTORE_CHECK.md",
    "compare_faiss*.py", "run_unit_checks.py", "freeze_identity.py", "snapshot_runtime.py",
    "report_revise.py", "report_render.py", "report_check_*.py", "report_draw_flow.py",
    "report_facts_contract.md", "report_runtime_flow.png", "report_runtime_flow.svg",
    "curate_evidence.py", "prepare_report_facts.py", "finalize_docs.py", "read_live_cases.py", "audit_live_content.py",
    "normalize_ui_usage_csv.py",
)
UI_FILES = {
    "capture_live_conversation.cjs", "verify_ui.cjs", "frontend_archive_search.json",
    "frontend_files.json", "logo_provenance.json", "ui_check_results.json",
    "UI_RESTORE.md", "ui_restored_desktop_initial.png", "ui_restored_mobile_initial.png",
}
GENERATED_FILES = {"INDEX_SHA256.json", "README.md", "server_traces_all.jsonl", "TRACE_SELECTION.json"}
DENIED_DIRECTORY_NAMES = {".git", ".venv", "venv", ".cache", "__pycache__", "node_modules"}
DENIED_EXTENSIONS = {".pyc", ".pyo", ".safetensors", ".bin", ".pt", ".pth", ".dll", ".exe"}
SECRET_PATTERNS = (
    ("groq_key", re.compile(rb"gsk_[A-Za-z0-9_-]{16,}")),
    ("tavily_key", re.compile(rb"tvly-(?:dev-|prod-)?[A-Za-z0-9_-]{16,}")),
    ("private_key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def denied(relative: PurePosixPath) -> bool:
    parts = [part.casefold() for part in relative.parts]
    if any(part in DENIED_DIRECTORY_NAMES or "chromium-profile" in part for part in parts):
        return True
    name = parts[-1] if parts else ""
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return True
    if name in {"credentials.json", "token.json", "id_rsa", "id_ed25519"}:
        return True
    suffix = relative.suffix.casefold()
    if suffix in DENIED_EXTENSIONS or suffix == ".docx":
        return True
    if suffix == ".pdf" and name != "stress.pdf":
        return True
    return "report_images" in parts or name.startswith("report_page_")


def scan_stream(stream, label: str) -> None:
    # A short carry also detects a token crossing a block boundary.
    carry = b""
    while True:
        block = stream.read(1024 * 1024)
        if not block:
            break
        data = carry + block
        for kind, pattern in SECRET_PATTERNS:
            if pattern.search(data):
                raise RuntimeError(f"Secret scan blocked {label}: {kind}; value not printed.")
        carry = data[-512:]


def scan_file(path: Path, label: str) -> None:
    with path.open("rb") as stream:
        scan_stream(stream, label)
    if path.suffix.casefold() == ".zip":
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                member_path = PurePosixPath(member.filename.replace("\\", "/"))
                if member_path.is_absolute() or ".." in member_path.parts or denied(member_path):
                    raise RuntimeError(f"Archive member excluded by packaging policy: {label}!{member.filename}")
                if member.file_size > 256 * 1024 * 1024:
                    raise RuntimeError(f"Unexpectedly large archive member: {label}!{member.filename}")
                with archive.open(member) as stream:
                    scan_stream(stream, f"{label}!{member.filename}")


def collect_files(work: Path) -> tuple[list[Path], list[str]]:
    candidates: set[Path] = set()
    excluded: list[str] = []

    def add_tree(root: Path) -> None:
        # Prune browser profiles before descending, instead of enumerating caches.
        for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            keep = []
            for name in dirs:
                folder = current_path / name
                relative = PurePosixPath(folder.relative_to(work).as_posix())
                if folder.is_symlink() or denied(relative):
                    excluded.append(relative.as_posix() + "/")
                else:
                    keep.append(name)
            dirs[:] = keep
            candidates.update(current_path / name for name in names)

    for pattern in TOP_LEVEL_PATTERNS:
        candidates.update(path for path in work.glob(pattern) if path.is_file())
    for directory in work.iterdir():
        if directory.is_dir() and any(directory.name.startswith(prefix) for prefix in DIRECTORY_PREFIXES):
            add_tree(directory)
    ui = work / "ui_restore"
    if ui.exists():
        candidates.update(path for path in ui.iterdir() if path.is_file() and path.name in UI_FILES)
        for folder in ui.glob("live_conversation_*"):
            if folder.is_dir():
                add_tree(folder)
    files = []
    for path in sorted(candidates):
        relative = PurePosixPath(path.relative_to(work).as_posix())
        if path.is_symlink() or denied(relative):
            excluded.append(relative.as_posix())
            continue
        path.resolve().relative_to(work.resolve())
        files.append(path)
    return files, excluded


def classify(relative: str) -> str:
    name = relative.casefold()
    if name.startswith("ui_restore/live_conversation_") or name.startswith("faiss_live"):
        return "live_response_or_failure; inspect recorded graph/status, not a quality score"
    if name.startswith("runtime_snapshots/") or "source_snapshot" in name or name.endswith("source_before_78b118f.zip"):
        return "source_snapshot"
    if "comparison" in name:
        return "real_local_retrieval_parameter_comparison; used_for_tuning"
    if "production_retrieval" in name:
        return "real_local_retrieval; no_provider; span_coverage_not_answer_accuracy"
    if name.startswith("ui_restore/"):
        return "ui_checks_or_initial_image; browser_response_checks_use_fixtures"
    if "tests" in name or name.startswith("pytest") or "unit" in name:
        return "unit_fixture_or_resource_failure_log; read_skips_and_exit_status"
    if name.startswith("report_"):
        return "report_script_contract_or_flow; no_draft_or_full_report"
    if "traces" in name or "diagnostic_" in name:
        return "raw_trace_or_diagnostic; success_refusal_and_errors_preserved"
    return "provenance_configuration_or_reproduction_script"


def select_traces(path: Path) -> tuple[bytes, dict]:
    if not path.is_file():
        raise RuntimeError(f"Trace source is missing: {path}")
    selected = []
    by_graph = Counter()
    by_suite = Counter()
    statuses = Counter()
    trace_ids = []
    total_lines = 0
    with path.open("rb") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            if not raw_line.strip():
                continue
            total_lines += 1
            try:
                record = json.loads(raw_line)
                stamp = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    raise ValueError("timestamp has no timezone")
            except (ValueError, KeyError, TypeError) as error:
                raise RuntimeError(f"Invalid trace metadata at line {line_number}; raw record not printed.") from error
            if stamp.astimezone(VN_TIMEZONE).date() != EVIDENCE_DATE:
                continue
            scan_stream(io.BytesIO(raw_line), f"selected trace line {line_number}")
            selected.append(raw_line)
            by_graph[str(record.get("graph_id"))] += 1
            by_suite[str(record.get("suite"))] += 1
            statuses[f"{record.get('http_status')}:{record.get('code')}"] += 1
            trace_ids.append(record.get("trace_id"))
    if not selected:
        raise RuntimeError("No trace records matched 05/11/2026 in Vietnam time.")
    # Keep every selected line, including repeated IDs if the original contains them.
    return b"".join(selected), {
        "date": EVIDENCE_DATE.isoformat(), "timezone": "+07:00",
        "source": ".cache/request_traces.jsonl", "source_lines_read": total_lines,
        "selected_lines": len(selected), "trace_ids": trace_ids,
        "by_graph": dict(by_graph), "by_suite": dict(by_suite), "by_http_and_code": dict(statuses),
        "transform": "Filter by Vietnam calendar date; selected original JSONL bytes unchanged.",
        "secret_scan": "passed; matching a secret would abort instead of redact raw evidence",
    }


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Copy after all final model runs are complete; otherwise only print a plan.")
    parser.add_argument("--work", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent / "CCNLTHD_LangGraph")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--expected-final-graph", default=EXPECTED_FINAL_GRAPH)
    parser.add_argument("--refresh", action="store_true", help="Refresh matching curated paths; never removes existing files.")
    args = parser.parse_args()
    work, repo = args.work.resolve(), args.repo.resolve()
    if work.name != WORKSPACE_NAME:
        raise RuntimeError("Unexpected work-folder name; verify --work explicitly in the script before changing scope.")
    destination = (args.destination or repo / "evidence" / "restored_20261105").resolve()
    destination.relative_to((repo / "evidence").resolve())
    identity = json.loads((repo / "docs" / "RESTORED_RUNTIME_IDENTITY.json").read_text(encoding="utf-8"))
    active_graph = identity["identity"]["graph_id"]
    if active_graph != args.expected_final_graph:
        raise RuntimeError(f"Final graph mismatch: manifest={active_graph}, expected={args.expected_final_graph}.")
    files, excluded = collect_files(work)
    if not files:
        raise RuntimeError("The selection contains no evidence files.")
    # Inspect the entire selection before writing any curated output.
    entries = []
    for path in files:
        relative = path.relative_to(work).as_posix()
        scan_file(path, relative)
        entries.append({"path": relative, "bytes": path.stat().st_size, "sha256": file_hash(path),
                        "category": classify(relative), "copy": "byte-identical"})
    trace_bytes, trace_metadata = select_traces(repo / ".cache" / "request_traces.jsonl")
    final_graph_trace_count = trace_metadata["by_graph"].get(args.expected_final_graph, 0)
    plan = {"mode": "execute" if args.execute else "read_only_plan", "source": str(work), "destination": str(destination),
            "selected_files": len(entries), "selected_bytes": sum(entry["bytes"] for entry in entries),
            "excluded_candidate_files": len(excluded), "selected_server_trace_lines": trace_metadata["selected_lines"],
            "expected_final_graph": args.expected_final_graph, "matching_final_graph_trace_lines": final_graph_trace_count,
            "model_or_word_calls": 0, "secret_scan": "passed"}
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0
    if not final_graph_trace_count:
        raise RuntimeError("No final-graph server trace exists yet. Run final live checks before executing curation.")
    intended_paths = {entry["path"] for entry in entries} | GENERATED_FILES
    existing = {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()} if destination.exists() else set()
    extra = existing - intended_paths
    if extra:
        raise RuntimeError("Destination contains files outside the current allowlist; inspect it before retrying. No files removed.")
    if existing and not args.refresh:
        raise RuntimeError("Destination already contains evidence. Use --refresh only after reviewing the new plan.")
    destination.mkdir(parents=True, exist_ok=True)
    for source, entry in zip(files, entries):
        target = destination / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if file_hash(target) != entry["sha256"] or file_hash(source) != entry["sha256"]:
            raise RuntimeError(f"Source changed or copied bytes differ: {entry['path']}")
    (destination / "server_traces_all.jsonl").write_bytes(trace_bytes)
    write_json(destination / "TRACE_SELECTION.json", trace_metadata)
    readme = f"""# Minh chứng khôi phục ngày 05/11/2026

Gói này chỉ lấy các nhóm tệp được chọn từ workspace, không sao chép cả thư mục làm việc. Mỗi tệp nguồn được đối chiếu SHA-256 sau khi copy; nội dung byte giữ nguyên. `INDEX_SHA256.json` liệt kê tệp và phạm vi. Không kèm .env, khóa API, .venv, cache model, hồ sơ Chromium, báo cáo Word/PDF hoặc hàng trăm ảnh trích từ báo cáo.

Graph cuối được yêu cầu khi xuất: `{args.expected_final_graph}`. Các lượt trong gói có thể thuộc nhiều graph khác nhau; phải đọc định danh trong từng log. Không thay graph của lượt cũ bằng graph cuối và không ghép câu trả lời giữa các lượt.

## Đọc kết quả

- `faiss_*comparison/` và retrieval production: embedding thật trong máy + FAISS. Bộ 27 câu đã dùng để sửa/chọn tham số; đủ span không phải đáp án model đúng và không phải đánh giá độc lập. Không gọi Groq/Tavily trong kiểm tra retrieval cục bộ.
- `ui_restore/ui_check_results.json`: kiểm tra Chrome dùng phản hồi fixture trong trình duyệt; không phải điểm nội dung. Ảnh initial chỉ có lời chào, không chứa câu trả lời model dựng sẵn.
- `ui_restore/live_conversation_*/` và `faiss_live*`: đọc raw request/response, trace, nguồn, usage, HTTP status và trạng thái trả lời/từ chối. Những lượt thiếu bằng chứng, lỗi xác thực, lỗi quota hoặc lỗi thiếu RAM vẫn giữ riêng. HTTP 200 hoặc quote khớp chưa đủ để kết luận nội dung đúng.
- Một số `LIVE_RESULTS.csv` UI cũ ghi số token đã quan sát dù usage chưa đầy đủ. Giữ nguyên các CSV gốc để bảo toàn provenance; dùng `LIVE_RESULTS_USAGE_NORMALIZED.csv` đi kèm để đối chiếu cột token: khi thiếu usage, các cột này để trống. `normalize_ui_usage_csv.py` tạo bảng riêng từ JSON, không thay ảnh, raw JSON hoặc CSV gốc. Không cộng token quan sát một phần thành tổng usage hoàn chỉnh.
- Unit XML/log: phân biệt số ca đạt, bỏ qua, lỗi và các lần chạy bị dừng. Tests dùng fixture không được tính là lượt model thật.
- `runtime_snapshots/`, snapshot source và source ZIP baseline giữ định danh từng lần. Thư viện và PDF được đối chiếu qua các lock; không kèm trọng số embedding.
- Script, hợp đồng dữ kiện và sơ đồ phục vụ tái lập thay đổi báo cáo. Các plan/validation bản nháp và bản Word/PDF đầy đủ không đưa vào Git; hồ sơ Word cuối được bàn giao riêng sau khi khóa commit.

`server_traces_all.jsonl` chứa **mọi dòng trace ngày 05/11/2026 theo giờ Việt Nam (+07:00)** tìm được trong nguồn tại lúc xuất. Chỉ lọc ngày, giữ nguyên byte mỗi dòng; không đổi câu trả lời, loại refusal hoặc khử trùng trace ID. `TRACE_SELECTION.json` ghi số dòng theo graph/suite/status. File đã qua kiểm tra mẫu khóa bí mật; nếu gặp khóa, script dừng trước khi copy thay vì xuất khóa hoặc sửa raw log. Bộ kiểm tra này không khẳng định đã nhận diện mọi dạng thông tin nhạy cảm có thể có.

Giữ nguyên các tệp lịch sử 154 mảnh và 9 snapshot trong `handover/`; số liệu và điểm người chấm cũ chỉ thuộc phản hồi đã được chấm. Không tự tạo điểm người thật cho bản khôi phục.

## Tái lập bước tuyển chọn

```powershell
.\\.venv\\Scripts\\python.exe ..\\{WORKSPACE_NAME}\\curate_evidence.py
.\\.venv\\Scripts\\python.exe ..\\{WORKSPACE_NAME}\\curate_evidence.py --execute --expected-final-graph {args.expected_final_graph}
```

Lệnh đầu chỉ in kế hoạch và quét bí mật. Chạy lệnh thứ hai sau khi các lượt cuối đã xong; script không gọi model hoặc Word. `--refresh` chỉ dùng khi chủ động cập nhật các đường dẫn đã tuyển chọn, không xóa tệp. SHA của chính INDEX không nằm trong INDEX để tránh tự tham chiếu.
"""
    (destination / "README.md").write_text(readme, encoding="utf-8")
    generated = []
    for name in ["README.md", "server_traces_all.jsonl", "TRACE_SELECTION.json"]:
        path = destination / name
        scan_file(path, name)
        generated.append({"path": name, "bytes": path.stat().st_size, "sha256": file_hash(path),
                          "category": "derived_index_readme_or_filtered_trace", "copy": "generated; see transform metadata"})
    index = {"created_at": datetime.now(VN_TIMEZONE).isoformat(), "source_workspace": WORKSPACE_NAME,
             "expected_final_graph": args.expected_final_graph, "copied_files": len(entries), "generated_files": len(generated),
             "files": entries + generated, "excluded_candidate_files": excluded,
             "copy_verification": "Every copied source/destination SHA-256 matched after copy.",
             "secret_scan": "passed for selected files, ZIP members and selected trace lines; no matching secret values printed",
             "model_or_word_calls": 0, "final_graph_trace_lines": final_graph_trace_count}
    write_json(destination / "INDEX_SHA256.json", index)
    print(f"Curated {len(entries)} byte-identical source files and {len(generated)} derived files; index written.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"Curation stopped: {error}", file=sys.stderr)
        raise SystemExit(1)
