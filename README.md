# Chatbot Hỗ trợ tâm lý — Nhóm 15

Ứng dụng dùng **FastAPI + LangGraph**, model **openai/gpt-oss-20b**. Bản khôi
phục ngày 05/11 dùng embedding tiếng Việt + FAISS và để model chọn công cụ
bằng tool calling. Giao diện được phục dựng theo ảnh trong báo cáo: logo SGU,
thanh bên, khung hội thoại màu hồng và ô gửi tin nhắn. Không tìm được HTML gốc
trong repo/gói lưu; logo được trích từ ảnh báo cáo. Câu trả lời lấy từ API thật,
không chép sẵn các phản hồi trong ảnh. Định danh source và cấu hình hiện tại ở
`docs/RESTORED_RUNTIME_IDENTITY.json`; các kết quả cũ được giữ riêng theo ngày.

## Cài đặt và chạy

Dùng Windows, Python **3.13.2**. Tại thư mục có `main.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Tự điền GROQ_API_KEY và TAVILY_API_KEY vào .env cục bộ.
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.verify_handover --strict
.\.venv\Scripts\python.exe start_api.py
```

Mở http://127.0.0.1:8000/ ; API tại `/docs`, định danh tại `/health`.
Chỉ dùng một worker vì cache/checkpoint lưu RAM. Giữ model mặc định ở trên.
`requirements.txt` dẫn tới **một lock duy nhất**: `requirements-locked.txt`.
Các recipe cũ ở `docs/historical_requirements/`, không cài chồng.
Không đưa `.env`, API key hoặc `.venv` vào Git/bài nộp.

Khi khởi động, ứng dụng chuẩn bị model embedding và chỉ mục PDF trước khi nhận
yêu cầu; đợi `Application startup complete` rồi mở giao diện. Model tải đúng
revision từ Hugging Face nếu chưa có cache. Bước chuẩn bị không gọi Groq, có
log riêng `.cache/rag_preparation.json`, không trừ thời gian này khỏi các số
đo cũ. Không đóng gói `.cache` hoặc hồ sơ trình duyệt. Giao diện giữ mã phiên
trong tab để gửi lịch sử nhiều lượt; dữ liệu phía server mất khi restart.

## Kiểm tra không gọi dịch vụ

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider tests
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.smoke_handover
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.check_rag_retrieval --output evidence_recheck
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.verify_final
```

Smoke dùng model/web fixture và PDF/embedding/FAISS thật. Không gọi đây là kết quả Groq/Tavily mới.
Hai ca unit cần model embedding thật được bỏ qua mặc định; có thể bật bằng
`RUN_LOCAL_EMBEDDING_TESTS=1`. Kiểm tra retrieval riêng dùng model thật và lưu
đủ đoạn/điểm/trang. Tắt demo trước khi chạy retrieval offline để không nạp hai
bản embedding cùng lúc trên máy ít RAM. Các script live chỉ chạy khi chủ động
dùng quota.

Chạy tám câu RAG cũ bằng Groq thật, dùng output chưa tồn tại:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.run_rag_live --base-url http://127.0.0.1:8000 --prepare-index --delay 30 --output ..\rag_live_recheck --ids rag_01 rag_02 rag_03 rag_04 rag_05 rag_06 rag_07 rag_08
```

Log chuẩn bị FAISS nằm riêng; không warm-up model hoặc retry tự động. Thiếu
token usage để `null` trong JSON và trống trong CSV. Bước kiểm tra strict đối
chiếu source hiện tại và kiểm tra nguyên vẹn dữ liệu lịch sử, không gán định
danh mới cho các log cũ.

Chế độ `--base-url` dùng API đang chạy và đọc trace của API đó, không nạp thêm
embedding trong một tiến trình server thứ hai.

## Nội dung code và minh chứng

- `agent.py`, `main.py`, `frontend/`: API `/chatbot`, model chọn RAG/web hoặc trả
  lời trực tiếp; nguồn được kiểm citation/quote. Chỉ thực thi tối đa một tool
  trong một lượt, chưa phải agent lập kế hoạch nhiều bước.
- `Stress.pdf`, `Rag_tool.py`, `faiss_retrieval.py`: checkpoint
  `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base` revision
  `608779b86741a8acd8c8d38132974ff04086b138`, PyVi, mean pooling, chuẩn hóa vector,
  FAISS IndexFlatL2; chunk tối đa 1000 ký tự, overlap 180, top-6. Khoảng cách L2
  bình phương nhỏ hơn nghĩa là gần hơn, không phải xác suất đáp án đúng.
- `retrieval.py`: BM25 lịch sử để đối chiếu, không làm fallback cho FAISS.
- `response_cache.py`: exact cache RAM TTL 300 giây, capacity 128. Bộ nhớ phiên
  dùng InMemorySaver; ID caller tự khai không phải cơ chế đăng nhập/phân quyền.
- `math_graph.py`: executor riêng, chưa gắn vào chatbot hoặc LLM tool choice.
- `handover/`: nguyên bản log/trace/context/usage, bộ đề và phiếu người chấm.
- `evidence/`: chat lịch sử, lỗi auth, các lượt kiểm tra có ngày và chỉ mục từng câu.
- `docs/`: bảng phủ, giới hạn, AI Disclosure, chỉ mục bộ đề và nhật ký thay đổi.
- `labs/`: bài tập độc lập có starter/solution; gói lab được phát riêng khi nộp.

RAG **BM25 lịch sử**: 5 hồi quy + 8 câu ngày 28/10; 13 phiếu đạt **96/104**.
Web **lịch sử 28/10**: 4 câu kỹ thuật, **2 trả lời/2 từ chối**, điểm **20/32**.
Một người chấm; web có Codex hỗ trợ, chưa thẩm định URL độc lập. Không quy các điểm
này thành độ chính xác hay hiệu quả lâm sàng. HTTP 200, quote khớp và retrieval có
đủ span là ba minh chứng riêng, không tự chứng minh đáp án đúng.

Các điểm người chấm, 57 test cũ và kết quả BM25 không phải kết quả của FAISS
khôi phục. Source v1.3 gốc còn nguyên trong
`handover/evidence/cache_memory_20261029/source_snapshots/` để kiểm hash.

Các README/metadata trong thư mục bằng chứng là ghi chú tại thời điểm xuất; giữ
nguyên cả lỗi, từ chối và trạng thái trước push. Nhật ký bản cuối ở `docs/JOURNAL.md`.
Word/notebook cũ, ảnh sinh báo cáo và launcher CLI không thuộc demo đã được loại
khỏi cây nộp; vẫn còn trong lịch sử Git. Báo cáo được nộp riêng cùng code.
