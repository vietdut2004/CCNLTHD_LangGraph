# Bảng phủ nội dung và minh chứng

Bản khôi phục ngày 05/11 dùng FAISS và tool calling, được khóa riêng trong
`docs/RESTORED_RUNTIME_IDENTITY.json`. Bảng đầu là **minh chứng lịch sử đến
03/11**, giữ nguyên kết quả của từng lượt; các số này không được gán cho source
khôi phục. Các kiểm tra ngày 05/11 được tách ở bảng tiếp theo.

Đường dẫn dưới đây tính từ thư mục gốc repository. Bảng CSV đi kèm giữ thêm phạm
vi và phương pháp của từng mảnh. Mỗi lượt được đọc theo ngày, source và model
riêng; hoàn tất kỹ thuật, tìm được đoạn và trả lời đúng là ba kết luận khác nhau.

| Mảnh | Kết quả được giữ | Minh chứng | Giới hạn chính |
|---|---|---|---|
| Source, requirements, PDF lịch sử | Runtime giữ byte của `60b2a03`; Python 3.13.2; PDF 6 trang; BM25 650/180/top-3 | `handover/EXPECTED_RUNTIME_IDENTITY.json`, `handover/evidence/cache_memory_20261029/source_snapshots/requirements-locked.txt`, `Stress.pdf`, `SOURCE_REGISTER.md` | Đây là lock lịch sử; requirements ở gốc hiện thuộc bản khôi phục. Hash không xác nhận thẩm quyền y khoa |
| Chat 20/10 | 10 câu cơ bản hoàn tất; 3 lỗi 422 mong đợi; 1 warm-up riêng | `evidence/historical/chat_20261020/` | Nguồn `01ad2c0`; chưa chấm nội dung |
| RAG 24/10 | 8 câu RAG: 3 trả lời, 5 từ chối; giữ đủ các bản ghi diagnostic trong bộ 18 | `handover/evidence/rag_8_20261024/` | FAISS, 500/50/top-2; AI audit tách khỏi điểm người thật |
| RAG lỗi xác thực | 2 lượt, mỗi lượt 1 lỗi HTTP 502; phần còn lại chưa chạy | `evidence/failures/rag_auth_initial_20261028/`, `evidence/failures/rag_auth_recheck_20261028/` | Không có đáp án model để chấm; thiếu usage là null trong chỉ mục |
| RAG BM25 hồi quy 28/10 | 5/5 hoàn tất, 5 phản hồi trả lời, 6.233 token | `handover/evidence/rag_regression_5_20261028/` | Cùng PDF; latency yêu cầu đầu gồm chuẩn bị PDF |
| RAG BM25 bộ mới 28/10 | 8/8 hoàn tất; 6 trả lời, 2 từ chối ngoài PDF; 11.454 token | `handover/evidence/rag_new_8_20261028/` | Nay là bộ hồi quy; không còn là dữ liệu chưa thấy khi dùng lại |
| Web 24/10 | 2 trả lời, 2 từ chối | `handover/evidence/web_4_20261024/` | Thiếu thời điểm riêng từng URL; không ghép đáp án giữa lượt |
| Web 28/10 | 4/4 hoàn tất; web_03/04 trả lời, web_01/02 từ chối; 12 nguồn, 8.653 token | `handover/evidence/web_4_20261028/` | Quote sai dẫn tới từ chối; bản nháp không phải phản hồi cuối |
| Retrieval BM25 | 27 câu, gồm 25 có đáp án và 2 ngoài PDF; đủ span 25/25 câu có đáp án | `evidence/indexes/RETRIEVAL_COVERAGE_PER_CASE.json`, `evidence/verification/windows_20261029/retrieval/` | Không phải 25/25 đáp án model đúng; BM25 không phải xác suất |
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


## Kiểm tra bản khôi phục ngày 05/11/2026

Minh chứng mới được tuyển chọn vào `evidence/restored_20261105/` và có `INDEX_SHA256.json`.
Các log lịch sử trong bảng trên giữ nguyên nguồn gốc. Runtime mới nhất dùng
graph `9df445c208d40dc57c00`; từng lượt trước vẫn giữ graph đã ghi khi chạy.

| Mảnh | Kết quả đã ghi | Minh chứng | Giới hạn |
|---|---|---|---|
| Source/lock/PDF | PhoBERT/PyVi + FAISS; chunk 1000, overlap 180, top-6; cùng checkpoint và PDF | `docs/RESTORED_RUNTIME_IDENTITY.json`, `docs/FINAL_SOURCE_LOCK.json`, `evidence/restored_20261105/EMBEDDING_AND_PDF_LOCK.json` | Runtime khác BM25; không gán số cũ sang bản mới |
| So sánh retrieval | Bản 500/50/top-2 không chuẩn hóa: 6/25 đủ span; cấu hình được chọn: 25/25 trên 27 câu, gồm 2 ngoài PDF | `evidence/restored_20261105/faiss_retrieval_comparison/`, `evidence/restored_20261105/faiss_final_production_retrieval/` | Embedding thật trong máy, không provider; đã dùng bộ câu để chọn tham số, không độc lập và không phải answer accuracy |
| Unit nhẹ | 67 đạt, 2 bỏ qua, tổng 69; 12.810 giây, 0 lỗi | `evidence/restored_20261105/unit_tests_light_final.xml` | Không provider; fixture chỉ kiểm tra cơ chế; ca bỏ qua không tính đạt |
| Giao diện fixture | 12/12 ca Chrome về bố cục/session/error/render | `evidence/restored_20261105/ui_restore/ui_check_results.json` | Phản hồi gửi/nhận dùng fixture; ảnh initial chỉ có lời chào; 0 provider call |
| UI thật, một phiên ba câu | HTTP 200/ok cả ba; lần lượt RAG, hội thoại, web | `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T16-33-55-604Z/` | Đúng một lượt được chọn, không ghép các lần thử; vẫn cần xem từng ý trả lời và nguồn |
| RAG thật, 13 câu | Hoàn tất kỹ thuật 13/13; 10 trả lời, 3 từ chối, 0 lỗi kỹ thuật | `evidence/restored_20261105/faiss_live_final_13/results.jsonl`, `summary.json`, `server_traces.jsonl` | 8 câu cũ + new_01/03/06 + 2 ngoài PDF; mode rag, cache tắt, concurrency 1, delay 45 giây, FAISS warm; không phải điểm nội dung |
| Các lần thử trước | 6 thư mục UI trước lượt được chọn, giữ cả lỗi/từ chối | `evidence/restored_20261105/ui_restore/live_conversation_*/`, `evidence/restored_20261105/server_traces_all.jsonl` | Không thay định danh hoặc lấy câu tốt ở lượt khác ghép vào kết quả cuối |
| Quote/source | Model chọn mã quote; server đổi về đoạn nguồn nguyên bản và kiểm tra lại | `agent.py`, trace `evidence_check`, model outputs/context trong từng lượt | Quote khớp chưa chứng minh quote đủ hỗ trợ toàn bộ câu trả lời; chưa có điểm người thật mới |
| Đối chiếu nội dung bằng Codex | Audit đủ 13 câu cùng trace của một lượt, gồm cả từ chối chưa phù hợp và citation chưa đủ | `evidence/restored_20261105/faiss_live_final_13/content_audit.json`, `content_audit.csv` | AI audit, không điểm người thật, không xác nhận lâm sàng hoặc đánh giá độc lập |
| Lịch sử | Giữ nguyên 154 tệp và 9 snapshot runtime, RAG 96/104, web 20/32 | `handover/`, `evidence/restored_20261105/verify_historical_integrity.json` | Điểm chỉ thuộc các phản hồi lịch sử đã chấm |

Latency và usage của UI và RAG được tính riêng trong `CHECK_REPORT.md`; không
lấy tổng của hai lượt làm latency của một phiên. Các token thiếu usage để null
hoặc trống. Không suy ra đáp án đúng từ HTTP 200 hoặc trạng thái `ok`.

- HTTP 200, trạng thái `ok` và quote khớp nguồn chỉ xác nhận một phần cơ chế; không đủ để chấm đáp án đúng.
- Bộ 27 câu retrieval đã dùng để sửa và chọn tham số. Kết quả 25/25 đủ span không phải đánh giá độc lập hoặc answer accuracy.
- `rag_06` vẫn từ chối dù retrieval có các span tham chiếu. Tìm được đoạn và tạo được câu trả lời là hai bước khác nhau.
- Các câu `rag_05`, `rag_07`, `new_03` có câu trả lời phù hợp tham chiếu nhưng quote chưa trực tiếp hoặc chưa đầy đủ cho ý được nêu. `rag_01` chỉ được audit là phần lớn có căn cứ, còn rút gọn bước giải thích và quote chưa trọn. Đây là đối chiếu của Codex, không phải điểm người thật.
- Không tự điền điểm người chấm cho lượt mới. RAG 96/104 và web 20/32 chỉ thuộc các phản hồi lịch sử đã được chấm.
- Hai ca unit nặng bị bỏ qua trong lượt kiểm tra nhẹ do điều kiện tài nguyên. Không tính chúng là đạt; giữ log của các lần thiếu RAM.
- FAISS/top-k mới có thể gửi ngữ cảnh dài hơn bản cũ. Không dùng latency hoặc token của BM25 để mô tả bản khôi phục.
