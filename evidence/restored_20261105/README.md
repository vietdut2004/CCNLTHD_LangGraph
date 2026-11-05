# Minh chứng khôi phục ngày 05/11/2026

Gói này chỉ lấy các nhóm tệp được chọn từ workspace, không sao chép cả thư mục làm việc. Mỗi tệp nguồn được đối chiếu SHA-256 sau khi copy; nội dung byte giữ nguyên. `INDEX_SHA256.json` liệt kê tệp và phạm vi. Không kèm .env, khóa API, .venv, cache model, hồ sơ Chromium, báo cáo Word/PDF hoặc hàng trăm ảnh trích từ báo cáo.

Graph cuối được yêu cầu khi xuất: `9df445c208d40dc57c00`. Các lượt trong gói có thể thuộc nhiều graph khác nhau; phải đọc định danh trong từng log. Không thay graph của lượt cũ bằng graph cuối và không ghép câu trả lời giữa các lượt.

## Đọc kết quả

- `faiss_*comparison/` và retrieval production: embedding thật trong máy + FAISS. Bộ 27 câu đã dùng để sửa/chọn tham số; đủ span không phải đáp án model đúng và không phải đánh giá độc lập. Không gọi Groq/Tavily trong kiểm tra retrieval cục bộ.
- `ui_restore/ui_check_results.json`: kiểm tra Chrome dùng phản hồi fixture trong trình duyệt; không phải điểm nội dung. Ảnh initial chỉ có lời chào, không chứa câu trả lời model dựng sẵn.
- `ui_restore/live_conversation_*/` và `faiss_live*`: đọc raw request/response, trace, nguồn, usage, HTTP status và trạng thái trả lời/từ chối. Những lượt thiếu bằng chứng, lỗi xác thực, lỗi quota hoặc lỗi thiếu RAM vẫn giữ riêng. HTTP 200 hoặc quote khớp chưa đủ để kết luận nội dung đúng.
- Một số `LIVE_RESULTS.csv` UI cũ ghi số token đã quan sát dù usage chưa đầy đủ. Giữ nguyên các CSV gốc để bảo toàn provenance; dùng `LIVE_RESULTS_USAGE_NORMALIZED.csv` đi kèm để đối chiếu cột token: khi thiếu usage, các cột này để trống. `normalize_ui_usage_csv.py` tạo bảng riêng từ JSON, không thay ảnh, raw JSON hoặc CSV gốc. Không cộng token quan sát một phần thành tổng usage hoàn chỉnh.
- Unit XML/log: phân biệt số ca đạt, bỏ qua, lỗi và các lần chạy bị dừng. Tests dùng fixture không được tính là lượt model thật.
- `runtime_snapshots/`, snapshot source và source ZIP baseline giữ định danh từng lần. Thư viện và PDF được đối chiếu qua các lock; không kèm trọng số embedding.
- Script, hợp đồng dữ kiện và sơ đồ phục vụ tái lập thay đổi báo cáo. Các plan/validation bản nháp và bản Word/PDF đầy đủ không đưa vào Git; hồ sơ Word cuối được bàn giao riêng sau khi khóa commit.

`server_traces_all.jsonl` chứa **mọi dòng trace ngày 05/11/2026 theo giờ Việt Nam (+07:00)** tìm được trong nguồn tại lúc xuất. Chỉ lọc ngày, giữ nguyên byte mỗi dòng; không đổi câu trả lời, loại refusal hoặc khử trùng trace ID. `TRACE_SELECTION.json` ghi số dòng theo graph/suite/status. File đã qua kiểm tra mẫu khóa bí mật; nếu gặp khóa, script dừng trước khi copy thay vì xuất khóa hoặc sửa raw log. Bộ kiểm tra này không khẳng định đã nhận diện mọi dạng thông tin nhạy cảm có thể có.

Giữ nguyên các tệp lịch sử 154 mảnh và 9 snapshot trong `handover/`; số liệu và điểm người chấm cũ chỉ thuộc phản hồi đã được chấm. Không tự tạo điểm người thật cho bản khôi phục.

## Tái lập bước tuyển chọn

```powershell
.\.venv\Scripts\python.exe ..\phuc_hoi_theo_bao_cao_20261105\curate_evidence.py
.\.venv\Scripts\python.exe ..\phuc_hoi_theo_bao_cao_20261105\curate_evidence.py --execute --expected-final-graph 9df445c208d40dc57c00
```

Lệnh đầu chỉ in kế hoạch và quét bí mật. Chạy lệnh thứ hai sau khi các lượt cuối đã xong; script không gọi model hoặc Word. `--refresh` chỉ dùng khi chủ động cập nhật các đường dẫn đã tuyển chọn, không xóa tệp. SHA của chính INDEX không nằm trong INDEX để tránh tự tham chiếu.
