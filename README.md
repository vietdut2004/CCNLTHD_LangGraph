# Bản bàn giao nhóm 15 evidence v1.3

Bản chọn là **evidence-v1.3-rag-check**, model `openai/gpt-oss-20b`. Chín file runtime giữ nguyên byte so với các log RAG/web thật ngày 28/10; API và frontend tại `/` dùng cùng `main:app`. BM25 cân bằng mục, chunk tối đa 650 ký tự, overlap mục tiêu 180, top-3; không cần embedding/FAISS cho bản chọn. Router theo mode/từ khóa; chưa phải agent tự lập kế hoạch. Toán là executor riêng, không gắn vào chatbot.

## Chạy demo trên Windows

Đứng tại thư mục chứa main.py, dùng Python 3.13.2 như lần đo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-locked.txt
Copy-Item .env.example .env
# Điền khóa của bạn trong .env trên máy; không gửi khóa vào chat/git.
.\.venv\Scripts\python.exe -m benchmarks.verify_handover --strict
.\.venv\Scripts\python.exe start_api.py
```

Mở http://127.0.0.1:8000/ để dùng frontend; `/docs` là giao diện API, `/health` chứa định danh. Bật một worker vì cache/checkpoint ở RAM. GROQ_API_KEY cần cho câu trả lời model; TAVILY_API_KEY thêm cho web. Thiếu khóa trả lỗi cấu hình, không thay bằng fixture. run_api.ps1 và run_api.bat đều gọi start_api.py từ đúng thư mục. Không mở trực tiếp frontend bằng file://.

## Kiểm tra không cần API key

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m benchmarks.smoke_handover
.\.venv\Scripts\python.exe -m benchmarks.export_handover
.\.venv\Scripts\python.exe -m benchmarks.check_rag_retrieval --output evidence_recheck
```

Smoke dùng LLM/web fixture và PDF thật, không chứng minh model trả lời đúng. verify_handover kiểm tra hash nguồn, log và môi trường; không gọi provider. graph_id có cả phiên bản thư viện: nếu môi trường khác lần đo, giữ ID thực của lần chạy mới. Không sửa ID/log để làm khớp. requirements-locked.txt là lock BM25 đã nhận từ Windows; requirements-live-locked.txt chỉ giữ cho stack FAISS lịch sử, không cài chồng cho bản chọn.

## Kết quả đã chốt

- RAG 28/10: 5 câu hồi quy có nguồn; 8 câu mới gồm 6 đáp án khớp PDF và 2 câu ngoài nguồn từ chối phù hợp theo đối chiếu AI. Huỳnh Lê Sơn chấm 13 câu: 96/104, trung bình 7,38/8; một người trên cùng PDF, không phải chuyên gia hoặc bộ dữ liệu độc lập.
- Web 28/10: 4/4 hoàn tất kỹ thuật; web_03/04 trả lời, web_01/02 từ chối do quote. Điểm người dùng chọn qua hội thoại có Codex hỗ trợ: 20/32, trung bình 5,00/8. Chưa thẩm định độc lập từng URL. Không lấy đáp án tốt từ lượt 24/10 ghép thành 4/4.
- 57 unit test trên source tích hợp đạt; đây là fixture/kiểm tra cục bộ, không phải 57 lượt provider. Cache/memory chỉ xác nhận cơ chế và dữ liệu truyền; chưa đo model thật nhớ đúng. Exact cache RAM TTL300/capacity128; ID do caller tự khai không phải đăng nhập/phân quyền.

handover/EVIDENCE_INDEX.json phân tách từng đợt và giới hạn. Raw/trace/usage/nguồn/điểm cùng bản xuất gốc nằm trong handover/evidence. Log có ngày trong mốc cũ được giữ nguyên; README trong từng thư mục evidence là ghi chú ở thời điểm xuất đó, không thay thế trạng thái ở README này. Chat 20/10 chỉ dẫn tới gói lịch sử, raw chat không có trong gói này.

## Trạng thái tích hợp

Source đã gom tại nhánh bàn giao cục bộ `codex/week8-evidence-v13`. GitHub main được đọc vẫn ở 01ad2c0; kiểm tra đẩy báo thiếu xác thực HTTPS. Chưa push/merge, chưa truy cập hoặc thay demo trên máy nhóm. Gói git bundle/patch và hướng dẫn Codex đi kèm để áp dụng trên máy có quyền, kiểm tra rồi đẩy nhánh. Không xem kết quả của bản mã riêng là kết quả demo đang triển khai.

Báo cáo gốc được quản lý tại https://docs.google.com/document/d/11cNh6hQX64hYrv2I_pGwWpW6c0LoIePp/edit ; các file Word/notebook có sẵn trong repository được giữ nguyên. README_EVIDENCE.md giải thích hợp đồng runtime, README_WEEK8.md chỉ tới bản bàn giao này. Lab độc lập ở labs/starter và labs/solution; phần bắt buộc không cần khóa trả phí. Giới hạn ứng dụng ở tra cứu/thông tin tham khảo; không suy hiệu quả lâm sàng hoặc khả năng phát hiện khủng hoảng.
