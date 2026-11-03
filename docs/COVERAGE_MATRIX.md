# Bảng phủ nội dung và minh chứng

Đường dẫn dưới đây tính từ thư mục gốc repository. Bảng CSV đi kèm giữ thêm phạm
vi và phương pháp của từng mảnh. Mỗi lượt được đọc theo ngày, source và model
riêng; hoàn tất kỹ thuật, tìm được đoạn và trả lời đúng là ba kết luận khác nhau.

| Mảnh | Kết quả được giữ | Minh chứng | Giới hạn chính |
|---|---|---|---|
| Source, requirements, PDF | Runtime giữ byte của `60b2a03`; Python 3.13.2; PDF 6 trang; BM25 650/180/top-3 | `handover/EXPECTED_RUNTIME_IDENTITY.json`, `requirements-locked.txt`, `Stress.pdf`, `SOURCE_REGISTER.md` | Commit nộp thêm hồ sơ; hash không xác nhận thẩm quyền y khoa |
| Chat 20/10 | 10 câu cơ bản hoàn tất; 3 lỗi 422 mong đợi; 1 warm-up riêng | `evidence/historical/chat_20261020/` | Nguồn `01ad2c0`; chưa chấm nội dung |
| RAG 24/10 | 8 câu RAG: 3 trả lời, 5 từ chối; giữ đủ các bản ghi diagnostic trong bộ 18 | `handover/evidence/rag_8_20261024/` | FAISS, 500/50/top-2; AI audit tách khỏi điểm người thật |
| RAG lỗi xác thực | 2 lượt, mỗi lượt 1 lỗi HTTP 502; phần còn lại chưa chạy | `evidence/failures/rag_auth_initial_20261028/`, `evidence/failures/rag_auth_recheck_20261028/` | Không có đáp án model để chấm; thiếu usage là null trong chỉ mục |
| RAG hồi quy 28/10 | 5/5 hoàn tất, 5 phản hồi trả lời, 6.233 token | `handover/evidence/rag_regression_5_20261028/` | Cùng PDF; latency yêu cầu đầu gồm chuẩn bị PDF |
| RAG bộ mới 28/10 | 8/8 hoàn tất; 6 trả lời, 2 từ chối ngoài PDF; 11.454 token | `handover/evidence/rag_new_8_20261028/` | Nay là bộ hồi quy; không còn là dữ liệu chưa thấy khi dùng lại |
| Web 24/10 | 2 trả lời, 2 từ chối | `handover/evidence/web_4_20261024/` | Thiếu thời điểm riêng từng URL; không ghép đáp án giữa lượt |
| Web 28/10 | 4/4 hoàn tất; web_03/04 trả lời, web_01/02 từ chối; 12 nguồn, 8.653 token | `handover/evidence/web_4_20261028/` | Quote sai dẫn tới từ chối; bản nháp không phải phản hồi cuối |
| Retrieval | 27 câu, gồm 25 có đáp án và 2 ngoài PDF; đủ span 25/25 câu có đáp án | `evidence/indexes/RETRIEVAL_COVERAGE_PER_CASE.json`, `evidence/verification/windows_20261029/retrieval/` | Không phải 25/25 đáp án model đúng; BM25 không phải xác suất |
| Unit/API 29/10 | Log ghi đạt 57 unit test, 7 ca trong tiến trình và 4 ca TCP | `evidence/verification/windows_20261029/` | Offline/fixture, không chứng minh chất lượng provider |
| Kiểm tra bản nộp 03/11 | Đạt strict 9 runtime/154 minh chứng và môi trường; 57 unit trong 10,50 giây; 7 ca trong tiến trình, 4 TCP; retrieval 25/25 câu có đáp án; 4 GET của `main:app` đều HTTP 200 | `evidence/verification/final_20261103/` | Hai câu ngoài PDF không chấm coverage; GET không key, không POST; 0 lần gọi provider |
| Cache/memory | 24 yêu cầu và 41 assertion có log đạt | `handover/evidence/cache_memory_20261029/` | RAM, đồng hồ ảo; chưa kiểm tra model thật nhớ đúng hoặc xác thực |
| Toán/router | 4 ca executor, 12 probe khớp luật; giữ hai giới hạn ngữ nghĩa | `handover/evidence/math_routing_20261029/` | Executor riêng; chưa có LLM chọn tool hoặc nối toán vào chatbot |
| Người chấm | RAG 96/104; web 20/32; giữ bản gốc và provenance | `handover/evidence/human_rag_13/`, `handover/evidence/human_web_4/` | Một thành viên, có hỗ trợ Codex; không phải đánh giá chuyên gia/độc lập |
| Báo cáo/source | Bản báo cáo tải 03/11 mô tả đúng hai lệch lịch sử về follow-up và latency | `docs/LIMITATIONS.md` | Sửa mô tả, không sửa tính năng hoặc số đo |
| Lab riêng | Chạy lại solution 03/11 đạt ba nhánh, một lỗi chủ động và phiên 1–2–1; giữ log cũ | `labs/`, `evidence/verification/final_20261103/`, `evidence/verification/windows_20261029/lab_metrics.jsonl` | Không gọi LLM; starter có TODO theo đề |

Chỉ mục 41 bản ghi HTTP tại `evidence/indexes/PER_CASE_RESULTS.json` dẫn tới raw
và trace của từng lượt, không thay thế bảng điểm nội dung. Kết quả lỗi/từ chối
có chỉ mục riêng ở `evidence/indexes/FAILURE_AND_REFUSAL_INDEX.json`. Xem
`QUESTION_ANSWER_INDEX.md` để tìm bộ câu hỏi và đáp án tham chiếu.
