# Nhật ký và phạm vi bản nộp cuối

Nhật ký này mô tả các hoạt động có minh chứng trong workspace, không phải bảng
chấm công hoặc nhật ký được người thật viết lại. Ngày giờ từng phép chạy nằm
trong `environment.json`, trace và `offline_commands.json` của đúng đợt.

| Mốc | Hoạt động | Minh chứng và giới hạn |
|---|---|---|
| 20/10/2026 | Đo hội thoại trên source cũ: 10 câu cơ bản, 3 đầu vào sai, 1 warm-up. | `evidence/historical/chat_20261020/`; không gán graph ID v1.3. |
| 24/10/2026 | RAG FAISS và web thật; giữ cả đáp án chưa đạt, từ chối và diagnostic. | `handover/evidence/rag_8_20261024/`, `web_4_20261024/`; không gộp với BM25. |
| 28/10/2026 | Sửa retrieval; hai lượt lỗi xác thực được giữ. Sau khóa hợp lệ, chạy 5 hồi quy + 8 câu mới RAG và 4 câu web. | `evidence/failures/`, `handover/evidence/*20261028/`; model gốc, không nới guard quote. |
| 28/10/2026 | Người dùng chấm RAG 13 câu và web 4 câu; Codex hỗ trợ rubric/ghi lại/xuất dữ liệu. | Giữ 96/104 và 20/32; một người, không chuyên gia/độc lập. |
| 29/10/2026 | Tích hợp worktree v1.3, strict, 57 unit test, smoke API/TCP, retrieval và lab. Push nhánh v1.3 sau khi quyền GitHub được cấp. | Log lịch sử giữ đúng ngày; main lúc đó chưa chứa bản bàn giao. |
| 03/11/2026 — chốt minh chứng | Khóa Git cục bộ, source/hash, PDF và bộ đề; xuất bản chốt v2 và lab riêng. | Không có provider call mới trong bước khóa này; giữ nguyên dữ liệu thô. |
| 03/11/2026 — chuẩn bị bài nộp | Đọc remote Git, fetch nhánh, tạo worktree final; đối chiếu báo cáo mới nhất và bộ source đã chốt. | Không sửa chín runtime đã đo. Bản báo cáo mới đã mô tả đúng UI chưa có follow-up và thời gian chuẩn bị PDF. |
| 03/11/2026 — dọn bản nộp | Loại 27 file Word/notebook/ảnh sinh/launcher cũ khỏi cây code; chuyển recipe requirements cũ vào tài liệu lịch sử; requirements.txt dẫn một lock chính. | Lịch sử Git còn nguyên; `CLEANUP_AND_PROVENANCE.json` liệt kê chính xác. Không xóa dữ liệu gốc của thành viên trong workspace. |
| 03/11/2026 — kiểm tra final | Chạy lại strict, 57/57 unit test, 7 ca API fixture, 4 ca TCP fixture, retrieval 25/25 câu có đáp án và lab. Kiểm tra GET ứng dụng main:app. | `evidence/verification/final_20261103/`; 0 provider call. Hai câu ngoài nguồn không tính coverage. Không tự chấm nội dung model mới. |
| 05/11/2026 — kiểm tra lại source và báo cáo | Đối chiếu giao diện và phương pháp RAG sau khi người dùng yêu cầu kiểm tra. Xác nhận bản chốt dùng biểu mẫu mới và BM25, khác ảnh chat và luồng Embedding + FAISS trong báo cáo. Fetch/pull trước khi sửa tiếp; remote main vẫn ở `78b118f`. | Giữ bản source trước sửa và thay đổi đang làm trong `evidence/restored_20261105/`; không ghi đè báo cáo nguồn hoặc gán số đo cũ sang bản sửa. |
| 05/11/2026 — khôi phục giao diện và RAG | Khôi phục bố cục chat theo ảnh báo cáo; nối nhiều lượt vào cùng phiên API. RAG trở lại embedding PhoBERT có PyVi và FAISS; giữ model Groq hiện có. | `docs/RESTORED_RUNTIME_IDENTITY.json`, thư mục `evidence/restored_20261105/ui_restore/`. Giao diện được dựng theo ảnh vì chưa tìm thấy HTML gốc. Không chép câu trả lời cũ vào giao diện. |
| 05/11/2026 — kiểm tra retrieval | Chạy embedding và FAISS thật trên 27 câu hồi quy, gồm 25 câu có đáp án và 2 câu ngoài nguồn; cấu hình được chọn là 1000/180/top-6, đủ span ở 25/25 câu có đáp án. | `evidence/restored_20261105/faiss_final_production_retrieval/`. Bộ câu hỏi đã dùng để sửa và chọn cấu hình, không phải bộ kiểm tra độc lập. Chỉ đo tìm đoạn, không phải 25 đáp án model đúng. Giữ cả cấu hình chưa đạt và log lỗi. |
| 05/11/2026 — kiểm tra giao diện | Kiểm tra bằng Chrome thật: 12/12 ca về bố cục, hội thoại nhiều lượt, giữ phiên, xử lý lỗi và hiển thị an toàn. | `evidence/restored_20261105/ui_restore/ui_check_results.json`. Hành vi gửi/nhận dùng fixture trong trình duyệt, 0 provider call; ảnh initial chỉ có lời chào. |
| 05/11/2026 — các lượt chat thật trong quá trình sửa | Giữ riêng 6 thư mục thử trước lượt UI cuối, gồm từ chối và lỗi; mỗi lượt giữ đúng graph, response và usage của nó. | `evidence/restored_20261105/ui_restore/live_conversation_*/`; không ghép câu trả lời giữa các lượt. |
| 05/11/2026 — kiểm tra unit trong điều kiện thiếu RAM | Lượt nhẹ cuối có 67 ca đạt, 2 ca bỏ qua, không lỗi; không gọi provider. | `evidence/restored_20261105/unit_tests_light_final.xml`; tổng 69 ca, 12.810 giây. Giữ các lần lỗi thiếu RAM; không tính ca bỏ qua là đạt. |
| 05/11/2026 — xác nhận bản khôi phục | Graph `9df445c208d40dc57c00` có một lượt UI ba câu riêng và một lượt RAG 13 câu đã ghi đủ. RAG hoàn tất kỹ thuật 13/13, trả lời 10, từ chối 3; chưa chấm đúng nội dung. | `evidence/restored_20261105/faiss_live_final_13/`, `evidence/restored_20261105/ui_restore/live_conversation_2026-11-05T16-33-55-604Z/`. Không gộp hai lượt để tính latency/usage; không tự thêm điểm người chấm. |

Commit code nộp và trạng thái remote thật được ghi trong `RELEASE_LOCK.json` ở
thư mục bài nộp cùng checksum của báo cáo/code/lab. File này được tạo từ commit
đã đọc lại sau khi xuất bản, không gán commit mới ngược cho các log cũ.

Các README/metadata dưới `handover/` hoặc thư mục lịch sử là ghi chú tại thời
điểm xuất. Ví dụ trạng thái “chưa push” hay “chat không nằm trong gói” ở tài liệu
cũ vẫn được giữ; bản nộp hiện đã bổ sung chat lịch sử trong `evidence/` và có
hồ sơ Git mới. Không sửa bản gốc để che quá trình hoặc kết quả thất bại.

Bản ngày 03/11 là baseline lịch sử dùng BM25 650/180/top-3. Bản khôi phục ngày
05/11 thay đổi runtime và requirements; không được tiếp tục mô tả là giữ nguyên
runtime của ngày 03/11. Định danh và hash mới nằm trong
`docs/RESTORED_RUNTIME_IDENTITY.json`; hồ sơ baseline được tách trong
`docs/FINAL_SOURCE_LOCK.json`. Các điểm RAG 96/104 và web 20/32 chỉ thuộc những
phản hồi đã được chấm trước đó.

## Ghi nhận cuối sau lượt RAG đủ 13 câu

Lượt UI được chọn giữ đúng ba trace `27807932154845fe8051681e33affcdb`, `f1b58d16d65e4ccb90ff050ff8ea1b6c` và `7738a52e3aa84b25882590fd6df1c2ba`. Lượt RAG chạy tuần tự, cách nhau 45 giây; FAISS đã chuẩn bị trước, không có request warm-up của benchmark. Cả hai dùng model `openai/gpt-oss-20b`. Xem `CHECK_REPORT.md` để đọc kết quả theo từng câu và giới hạn, không dùng số HTTP hoàn tất thay cho độ đúng.
