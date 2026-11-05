# Ba câu trong ảnh báo cáo — lượt chạy mới ngày 05/11/2026

Đã chạy bằng giao diện đang phục vụ tại `http://127.0.0.1:8000/`, cùng một phiên trò chuyện. Trước khi gửi câu hỏi, `/health` xác nhận `fixture:false`, model `openai/gpt-oss-20b`, graph `5200e395426bb2a4f7e0`. Không dùng đáp án mẫu, không giả lập phản hồi và không tự gửi lại khi có lỗi.

Thời điểm bắt đầu các câu lần lượt là 20:28:15, 20:28:20 và 20:28:22 ngày 05/11/2026, giờ Việt Nam. Nhật ký JSON giữ giờ UTC. Latency dưới đây đo từ trình duyệt, bao gồm thời gian chờ HTTP; không đồng nhất với thời gian sinh token của model.

| Câu | Kết quả API | Nhánh | Latency | Input / output token |
|---|---|---|---:|---:|
| Ý nghĩa của hít thở sâu | HTTP 200, `ok` | `answer` | 5.563 s | 455 / 829 |
| Bạn có khỏe không | HTTP 200, `ok` | `answer` | 1.572 s | 1.233 / 85 |
| Gợi ý phim truyền động lực | HTTP 200, `refused`, `INSUFFICIENT_EVIDENCE` | `web` | 6.931 s | 2.968 / 622 |

## Điều quan sát được

Giao diện hiển thị đủ các lượt, giữ đúng phiên, hiện câu trả lời và thông tin trace. Câu thứ ba nhận được phản hồi từ chối vì thiếu bằng chứng. Vì vậy, lượt này chưa tái hiện được danh sách phim trong ảnh cũ, dù cả ba HTTP response đều có mã 200.

Câu đầu được model trả lời trực tiếp, không có nguồn PDF trong response. Nội dung còn lặp ở phần định nghĩa và dùng cùng cụm “hệ thống thần kinh giao cảm” cho hai tác động đối lập. Đây là điểm cần xem lại nội dung, không được ghi thành kết quả đạt chỉ vì request hoàn tất.

Cả ba response đều có `sources:[]`. Lượt này không chứng minh chất lượng FAISS hay khả năng trích dẫn nguồn web. Trace của nhánh web cần được đối chiếu với log truy xuất để xác định nguyên nhân từ chối. Không tự suy đoán rằng API tìm kiếm không chạy.

Đây là ghi nhận kỹ thuật và quan sát nội dung; không có điểm người chấm mới. Các kết quả BM25, số liệu cũ và điểm đã chấm trước đó vẫn giữ nguyên nguồn gốc.

## Tệp đối chiếu

- `requests_responses.json`: request, response body gốc, response JSON, HTTP status/header, thời điểm, latency.
- `LIVE_CAPTURE_REPORT.json`: định danh backend, nguồn và usage theo từng câu.
- `LIVE_RESULTS.csv`: bảng xuất từ response thật; token thiếu dữ liệu sẽ để trống, không thay bằng 0.
- `turn_1_actual.png` đến `turn_3_actual.png`: ảnh sau từng lượt.
- `conversation_actual.png`: ảnh viewport cuối; `conversation_actual_full.png`: ảnh tăng chiều cao viewport để nhìn đủ hội thoại, không sửa nội dung tin nhắn.

Các trace lần lượt: `7e20e906950e423290b5231267bd482e`, `d51cbc1198214cc98c47b1fc25ca610c`, `a6e281dc82364e5c9f28bbba2ca52ca6`.
