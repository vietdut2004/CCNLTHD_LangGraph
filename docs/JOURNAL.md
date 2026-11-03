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

Commit code nộp và trạng thái remote thật được ghi trong `RELEASE_LOCK.json` ở
thư mục bài nộp cùng checksum của báo cáo/code/lab. File này được tạo từ commit
đã đọc lại sau khi xuất bản, không gán commit mới ngược cho các log cũ.

Các README/metadata dưới `handover/` hoặc thư mục lịch sử là ghi chú tại thời
điểm xuất. Ví dụ trạng thái “chưa push” hay “chat không nằm trong gói” ở tài liệu
cũ vẫn được giữ; bản nộp hiện đã bổ sung chat lịch sử trong `evidence/` và có
hồ sơ Git mới. Không sửa bản gốc để che quá trình hoặc kết quả thất bại.
