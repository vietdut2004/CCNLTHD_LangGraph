import json
from metrics import observe
from lab_graph import ask

cases = [("A1", "", "clarify"),
         ("A2", "LangGraph là gì?", "lookup"),
         ("A3", "Xin chào", "answer")]
rows, checks = [], []
for case_id, question, expected in cases:
    result, row = observe(
        lambda q=question, tid=case_id: ask(q, tid), case_id)
    checks.append(row["status"] == "ok"
                  and result.get("branch") == expected)
    rows.append(row)
    print(case_id, row["status"], result.get("branch"))

_, fault = observe(lambda: ask("!error", "fault-1"),
                   "A4", group="fault_injection")
checks.append(fault["status"] == "error"
              and fault["error_type"] == "RuntimeError")
rows.append(fault)
with open("lab_metrics.jsonl", "w", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
assert all(checks), "Có ca không đạt; xem lab_metrics.jsonl"
assert ask("LangGraph lượt 1", "memory-1")["turns"] == 1
assert ask("LangGraph lượt 2", "memory-1")["turns"] == 2
assert ask("LangGraph phiên mới", "memory-2")["turns"] == 1
print("PASS: 3 nhánh, 1 lỗi chủ động, 2 thread; đã ghi JSONL.")
