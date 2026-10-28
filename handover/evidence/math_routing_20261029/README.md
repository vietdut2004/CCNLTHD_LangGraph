# Tái lập kiểm tra việc số 4

Gói là bằng chứng offline, không chứa khóa và không thay toàn bộ dự án. Không cần chấm người thật cho các phép kiểm tra kỹ thuật này.

Dùng source hiện tại sau việc số 3, cùng venv đã cài requirements-locked.txt. So sánh hash của hai file trong source_snapshots/ với dự án nếu cần; đây là bản lưu để đọc/đối chiếu, không phải thư mục dự án đầy đủ để chạy riêng.

Chép duy nhất benchmarks/check_math_routing.py vào source/benchmarks/. Mở PowerShell tại source/:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.check_math_routing --output ..\kiem_tra_toan_router_viec4_lan1
.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider tests/test_evidence.py::test_math_actual_tool_invocations tests/test_evidence.py::test_full_trace_routes
```

Dùng tên output mới nếu đã chạy trước đó. Không cần API key; script tiêm adapter bị chặn hoặc model fixture để không gọi nhà cung cấp. Không đổi math_graph.py/agent.py để làm các probe đẹp hơn. Nếu runtime khác hash, ghi đúng phiên bản và đọc diff; không gán kết quả trong gói cho source khác.

Đọc CHECK_REPORT.md trước khi diễn giải số liệu. Giữ riêng ba nhóm: executor bốn ca, classify mười hai probe và một probe API dùng fixture. Không gộp chúng thành tỷ lệ đúng của model hoặc khả năng giải toán nhiều bước. Giới hạn từ khóa giao nhau/phủ định là quan sát thực tế, không tự sửa thành kết quả đạt theo ý định.

Script có thể giao cho Codex chạy lại tại máy để xác minh source đã tích hợp. Không yêu cầu gọi thêm model, đổi provider hoặc mua khóa. Bản báo cáo gốc được sửa có chọn lọc; gói này không dùng để chép đè Word, merge repo hoặc deploy.
