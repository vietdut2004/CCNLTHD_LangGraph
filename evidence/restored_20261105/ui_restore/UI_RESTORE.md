# Khôi phục giao diện theo ảnh trong báo cáo

Giao diện được đối chiếu với `report_images/image105.png`, trích từ bản `report_current.docx` đã tải ngày 05/11/2026. SHA-256 của tệp Word: `5ac33d056def26f9d0ad50f2effdd73e5a7f622567d5a2c71258ecc59a2bb3cb`.

Đã tìm HTML trong các thư mục làm việc, Downloads và các gói ZIP lưu từ những lần bàn giao trước. Các tệp tìm được đều là biểu mẫu thêm sau; chưa tìm thấy HTML của giao diện trong ảnh. Danh sách gói đã kiểm tra nằm trong `frontend_archive_search.json`. Vì vậy, phần trình bày lần này được khôi phục theo ảnh, không được xem là bản sao của mã frontend gốc.

## Những phần khôi phục

- Thanh bên nền trắng chiếm 20% chiều ngang, logo SGU và hai dòng “Hỗ trợ tâm lý”, “Chatbot đồng hành”.
- Tiêu đề và dòng giới thiệu giống ảnh; vùng hội thoại nền tím rất nhạt, tin người dùng màu hồng, tin chatbot màu trắng.
- Ô nhập ở dưới cùng, nút “Gửi” màu hồng và dòng Conversation ID. Mã phiên hiển thị là mã đang gửi tới API, thay cho chữ “free version” trong ảnh cũ.
- Lời chào ban đầu giống ảnh. Các câu trả lời trong cuộc trò chuyện được lấy từ API; không chép câu trả lời lịch sử vào mã giao diện.
- Lưu các lượt trò chuyện trong cùng tab. Cùng một `user_id` và `session_id` được gửi qua các lượt; Enter để gửi, Shift+Enter để xuống dòng.
- Nguồn và thông tin phản hồi nằm trong mục mở rộng bên dưới từng câu trả lời, không chiếm chỗ của khung trò chuyện.

Logo được cắt trực tiếp từ ảnh báo cáo tại vùng `(28,118)-(73,163)`, kích thước 45×45 pixel. `logo_provenance.json` lưu đường dẫn và hash. Đây là ảnh lấy từ minh chứng đã có, không phải logo vẽ mới. Khi phóng lớn, độ nét bị giới hạn bởi ảnh gốc.

## Kiểm tra

Chạy khi API đã phục vụ `/frontend`:

```powershell
node .\phuc_hoi_theo_bao_cao_20261105\ui_restore\verify_ui.cjs http://127.0.0.1:8000/
```

Script mở Chrome bằng hồ sơ riêng, chụp trang thật ở kích thước 1919×929 và 390×844. Ảnh desktop dùng kích thước vùng trang trong ảnh báo cáo, bỏ thanh địa chỉ và thanh tác vụ Windows.

Các bước kiểm tra hai lượt chat, khóa nút khi đang chờ, hiện lỗi, giữ phiên sau tải lại, xử lý URL và văn bản không an toàn dùng **phản hồi fixture trong trình duyệt**. Những bước này chỉ kiểm tra giao diện; không gọi Groq/Tavily và không chứng minh chất lượng trả lời. Kết quả được ghi riêng trong `ui_check_results.json`. Các ảnh mang tên `initial` chỉ có lời chào, không chứa các câu trả lời fixture.

Kết quả ngày 05/11/2026: **12/12 kiểm tra đạt**, không gọi provider. Đã mở và xem cả hai ảnh sau khi chụp. `ui_restored_desktop_initial.png` khớp bố cục chính của ảnh báo cáo; `ui_restored_mobile_initial.png` xác nhận ô nhập và nút gửi vẫn nằm trong màn hình nhỏ.

Ảnh báo cáo cũ có lịch sử hội thoại và thanh cuộn. Trang mới mở không chèn lại lịch sử đó. Thanh cuộn sẽ xuất hiện khi hội thoại dài. Trên điện thoại, thanh bên được ẩn để đủ chỗ cho nội dung.

Số liệu và phản hồi của những lần chạy cũ không được sửa hoặc gán cho giao diện vừa khôi phục.

## Chụp cuộc trò chuyện thật

Sau khi chốt backend, dùng lệnh sau để chạy ba câu trong ảnh báo cáo bằng API đang phục vụ. Script không chứa đáp án mẫu và không tự chạy lại khi có lỗi:

```powershell
node .\phuc_hoi_theo_bao_cao_20261105\ui_restore\capture_live_conversation.cjs --run-live http://127.0.0.1:8000/
```

Kết quả nằm trong thư mục mới `live_conversation_<UTC>`, gồm request, response gốc, nguồn, trace, usage, thời điểm và ảnh chụp sau từng lượt. Đây là lượt chạy mới; không dùng lại ngày, số đo hoặc điểm người chấm của những lượt cũ. Script không chấm đúng sai nội dung.
