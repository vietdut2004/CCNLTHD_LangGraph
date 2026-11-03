# Minh chứng bổ sung của bản nộp cuối

`handover/evidence/` giữ nguyên các log nguồn đã chốt; manifest gốc kiểm tra
154 file. Thư mục `evidence/` này bổ sung phần cần cho bài nộp đầy đủ:

- `failures/`: hai lượt Groq lỗi xác thực và các lỗi quyền GitHub trước khi push được.
- `historical/chat_20261020/`: raw chat cũ, cùng ba ca 422 và warm-up tách riêng.
- `indexes/`: bộ câu hỏi/đáp án, 41 bản ghi HTTP nối với trace, 27 ca retrieval,
  và chỉ mục lỗi/từ chối. Đường dẫn đã đổi theo cấu trúc repository, có provenance.
- `verification/windows_20261029/`: kết quả kiểm tra trên Windows ngày 29/10.
- `verification/final_20261103/`: các phép chạy lại khi chốt source cuối.

Usage thiếu metadata được để null/CSV trống ở chỉ mục dẫn xuất. `observed_tokens=0`
trong raw cũ chỉ là tổng quan sát, không có nghĩa đã biết hóa đơn hoặc token bằng 0.
Không sửa các raw này; xem `usage_complete` trước khi diễn giải.

Kết quả fixture, retrieval PDF thật và provider thật có phạm vi riêng. Không dùng
HTTP 200, quote khớp hoặc có đủ span để tự chấm đáp án model đúng. Bộ câu hỏi
đã chạy nay là hồi quy; không nhận là tập kiểm tra độc lập chưa từng xem.
