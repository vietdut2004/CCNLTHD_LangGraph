# Điểm do người thật xuất — đã kiểm tra

Người chấm ghi tên: Huỳnh Lê Sơn. Ngày chấm thực tế đã xác nhận: 28/10/2026.
JSON/CSV đủ 13 câu, bốn điểm mỗi câu trong 0–2, tổng khớp và trace/graph/đáp án
khớp 13 phản hồi trong phiếu. Không có điểm hoặc nhận xét do Codex điền thay.

Tổng rubric **96/104**, trung bình **7.38/8**.
5 câu hồi quy: **7.60/8**;
8 câu mới: **7.25/8**.
Điểm rubric không phải tỷ lệ câu trả lời đúng; không tự đặt ngưỡng đạt/trượt.

| Ca | Căn cứ/đủ ý | Liên quan | Phạm vi | Nguồn | Tổng |
|---|---:|---:|---:|---:|---:|
| rag_03 | 1 | 2 | 2 | 2 | 7/8 |
| rag_05 | 2 | 2 | 2 | 2 | 8/8 |
| rag_06 | 2 | 1 | 2 | 2 | 7/8 |
| rag_07 | 2 | 2 | 2 | 2 | 8/8 |
| rag_08 | 2 | 2 | 2 | 2 | 8/8 |
| heldout_01 | 2 | 1 | 1 | 1 | 5/8 |
| heldout_02 | 2 | 2 | 2 | 2 | 8/8 |
| heldout_03 | 2 | 1 | 2 | 2 | 7/8 |
| heldout_04 | 2 | 2 | 2 | 2 | 8/8 |
| heldout_05 | 2 | 2 | 2 | 2 | 8/8 |
| heldout_06 | 2 | 2 | 2 | 2 | 8/8 |
| heldout_07 | 2 | 2 | 2 | 1 | 7/8 |
| heldout_08 | 2 | 2 | 2 | 1 | 7/8 |

## Bảo toàn và sửa ngày theo xác nhận

Hai file trong original_exports/ được giữ nguyên byte, vẫn ghi ngày 28/11/2026.
Người dùng xác nhận ngày thực tế là 28/10/2026; hai file CHAM_NGUOI_THAT.json/.csv
ở thư mục này chỉ sửa reviewed_on trong 13 dòng, giữ nguyên mọi điểm, tên và nhận
xét. VALIDATION_AND_SUMMARY.json lưu checksum gốc và kiểm tra nhất quán.
Không sửa file gốc ở Downloads. Các file DIEM_CHO_NGUOI_THAT_CHAM cũ chỉ là khung,
không dùng làm điểm đã chấm; file điểm đã xác nhận nằm ở human_review/.

## Phạm vi kết quả

Một người chấm 13 câu từ cùng PDF (5 câu hồi quy và 8 câu mới gồm 2 câu ngoài PDF).
Phiếu không thu vai trò người chấm; không tự nhận là chuyên gia hoặc chấm độc lập.
Giữ nhận xét nguyên văn để đối chiếu; không thay đánh giá của người chấm bằng
đánh giá AI. Chưa đánh giá độ nhất quán giữa nhiều người, hiệu quả y khoa hoặc
chất lượng trên dữ liệu ngoài tập này. Chưa sửa báo cáo Word, push hay deploy.
