# Chỉ mục câu hỏi, đáp án tham chiếu và phản hồi

Các đường dẫn trong bảng tính từ thư mục gốc repository. File JSON giữ câu hỏi,
đáp án tham chiếu và metadata nguyên gốc; phản hồi thực tế nằm trong `results`
và `model_outputs`, không lấy từ đáp án tham chiếu. Các chỉ mục có đường dẫn đã
đổi theo bản nộp nằm trong `evidence/indexes/`.

| Bộ | Số câu | Câu hỏi và đáp án tham chiếu | Kết quả cần đối chiếu |
|---|---:|---|---|
| RAG hồi quy 28/10 | 5 | `handover/evidence/rag_regression_5_20261028/test_cases.json` | `results.json`, `retrieval_contexts.jsonl`, `server_traces.jsonl` cùng thư mục |
| RAG bộ mới ở thời điểm 28/10 | 8 | `handover/RAG_NEW_8_FROZEN.json`; bản đầu vào của runner tại `handover/evidence/rag_new_8_20261028/test_cases.json` | 6 phản hồi trả lời và 2 từ chối; raw cùng thư mục runner |
| Web 28/10 | 4 | `handover/WEB_4_FROZEN.json`; bản đầu vào của runner tại `handover/evidence/web_4_20261028/test_cases.json` | `results.json`, `web_contexts.jsonl`, `model_outputs.jsonl`, `server_traces.jsonl`; chỉ phản hồi API cuối được chấm |
| Retrieval PDF offline | 27 | `benchmarks/rag_check_cases.json` | `evidence/indexes/RETRIEVAL_COVERAGE_PER_CASE.json`; raw tại `evidence/verification/windows_20261029/retrieval/results.jsonl` |
| RAG lịch sử 24/10 | 18 bản ghi trong bộ runner | `handover/evidence/rag_8_20261024/test_cases.json` | Có 8 câu RAG cùng các ca diagnostic/cache/validation; không coi cả 18 là bộ RAG độc lập |
| Web lịch sử 24/10 | 4 | `handover/evidence/web_4_20261024/test_cases.json` | Giữ riêng graph ID, context và kết quả của ngày 24/10 |
| RAG lỗi xác thực lần đầu 28/10 | 16 câu dự kiến, 1 đã gọi | `evidence/failures/rag_auth_initial_20261028/test_cases.json` | 1 lỗi xác thực; phần còn lại chưa thực hiện |
| RAG kiểm tra lại xác thực 28/10 | 5 câu dự kiến, 1 đã gọi | `evidence/failures/rag_auth_recheck_20261028/test_cases.json` | 1 lỗi xác thực; không có đáp án model thật để chấm |
| Chat lịch sử 20/10 | 14 | `evidence/historical/chat_20261020/test_cases.json` | 10 câu cơ bản, 3 đầu vào sai mong đợi và 1 warm-up tách riêng |

Bộ retrieval 27 câu gồm 8 câu cũ, 6 câu bổ sung, 5 câu validation và 8 câu đã đóng
băng cho lượt mới; 25 câu có đáp án và 2 câu ngoài PDF. Các tập thành phần còn ở
`benchmarks/week8/` và `handover/RAG_NEW_8_FROZEN.json`. Không cộng lại các tập có
giao nhau thành số câu độc lập lớn hơn. Kiểm tra lại ngày 03/11 vẫn đủ span ở
25/25 câu có đáp án; hai câu ngoài PDF không chấm coverage. Log mới được giữ
tại `evidence/verification/final_20261103/`, tách khỏi raw 29/10.

Các file đầu vào đóng băng và bản runner có thể khác hash vì khác cấu trúc hoặc
metadata. Hash từng file được liệt kê trong
`evidence/indexes/QUESTION_ANSWER_DATASETS.json`; không yêu cầu hai file có nội
dung câu hỏi tương ứng phải có cùng hash. Bộ tám câu RAG đóng băng có SHA256
`8d512cb241a64330f88fa6e1bfbff7828255c73a99069c1ffd1dee209ff32a6c`, bộ bốn câu web
có SHA256 `cef7f538324e6e0ff3e8616197b9bd5ebe298dc4ed1410910b28c8e3bb48a4d3`.

Để lần theo từng câu, dùng `evidence/indexes/PER_CASE_RESULTS.json` hoặc CSV:
chọn đúng tên lượt và `case_id`, mở raw theo đường dẫn/chỉ số bản ghi, rồi nối
`trace_id` với trace cùng lượt. Chỉ mục này giữ 41 bản ghi HTTP có phạm vi riêng,
không phải 41 câu độc lập hoặc 41 phản hồi đạt nội dung. Chỉ mục lỗi/từ chối ở
`evidence/indexes/FAILURE_AND_REFUSAL_INDEX.json`.

Điểm người chấm được giữ tại `handover/evidence/human_rag_13/` và
`handover/evidence/human_web_4/`, kèm bản xuất gốc/provenance. HTTP 200, đủ span
truy xuất hoặc quote khớp không tự chứng minh đáp án đúng. Các tham chiếu có AI
hỗ trợ; xem `AI_DISCLOSURE.md` và `LIMITATIONS.md` trước khi diễn giải kết quả.
