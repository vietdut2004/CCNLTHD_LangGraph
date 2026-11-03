# AI Disclosure — bản nộp ngày 03/11/2026

Codex hỗ trợ đọc và đối chiếu source với báo cáo, sửa retrieval RAG, viết script
kiểm thử, truy vết lỗi, tổ chức dữ liệu, tạo chỉ mục, soạn tài liệu và đóng gói.
Codex cũng hỗ trợ soạn câu hỏi và đáp án tham chiếu từ PDF hoặc tài liệu kỹ thuật.
Các đáp án này là tham chiếu có AI hỗ trợ, chưa phải nhãn vàng do một nhóm độc lập
xây dựng. Việc AI tạo hoặc kiểm tra mã không tự chứng minh mã đúng.

Các lượt Groq/Tavily thật có ngày chạy, định danh nguồn, phản hồi, trace và usage
riêng. Kết quả fixture/offline được giữ riêng, không dùng latency hoặc token của
fixture làm số liệu model thật. Lượt chuẩn bị bản nộp ngày 03/11 thống nhất tài
liệu, cấu trúc, requirements và minh chứng; không tạo thêm phản hồi provider để
thay các câu từng sai hoặc từ chối. Ngày 03/11, Codex chạy strict, 57 unit test,
7 ca trong tiến trình, 4 ca TCP, retrieval trên PDF và solution lab. Các kiểm tra
này đạt và có log riêng trong `evidence/verification/final_20261103/`. Các trang
`/`, `/docs`, `/health`, `/openapi.json` của `main:app` đều trả HTTP 200 khi GET,
không dùng fixture. Lượt GET không có API key và không gọi POST chatbot; không
được dùng để kết luận provider hoạt động hoặc chấm nội dung. Tổng số lần gọi
provider trong lượt chốt là 0.

Huỳnh Lê Sơn chọn điểm và nhận xét của 13 câu RAG và 4 câu web. Codex hướng dẫn
rubric, trình bày phản hồi để đối chiếu, ghi lại lựa chọn và xuất JSON/CSV. Phần
web được chấm qua hội thoại có trợ giúp. Đây là một người chấm thuộc nhóm, chưa
phải đánh giá chuyên gia hoặc thẩm định độc lập từng URL. Giữ nguyên tổng RAG
**96/104** và web **20/32**, cùng nhận xét và hồ sơ gốc. Ngày chấm RAG được chuẩn
hóa từ 28/11 thành 28/10 theo xác nhận; bản xuất ban đầu và provenance vẫn còn.

Bộ câu hỏi đã dùng nay là bộ hồi quy, không còn là câu hỏi chưa thấy khi dùng lại.
Điểm rubric, kiểm tra quote và độ phủ đoạn truy xuất được báo cáo riêng; không đổi
chúng thành tỷ lệ trả lời đúng, khả năng đồng cảm hoặc hiệu quả lâm sàng.

Runtime đã đo được giữ nguyên byte so với bản `60b2a03`; commit nộp còn bao gồm
việc dọn file tham khảo và thống nhất hồ sơ. Xem định danh và hash trong hồ sơ
khóa nguồn của bản nộp, thay vì gán commit mới ngược cho log lịch sử.
