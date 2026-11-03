# Nhóm 15 — Bản nộp cuối LangGraph

Chatbot tham khảo dùng **FastAPI + LangGraph**, model **openai/gpt-oss-20b**.
Runtime được đo ngày 28/10 là `evidence-v1.3-rag-check`, graph ID
`beebab186d50bedb4180`; chín file runtime và PDF giữ nguyên byte. Bản cuối chỉ
thống nhất tài liệu, requirements, minh chứng và loại file làm việc cũ.

## Cài đặt và chạy

Dùng Windows, Python **3.13.2**. Tại thư mục có `main.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Tự điền GROQ_API_KEY và TAVILY_API_KEY vào .env cục bộ.
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.verify_handover --strict
.\.venv\Scripts\python.exe start_api.py
```

Mở http://127.0.0.1:8000/ ; API tại `/docs`, định danh tại `/health`.
Chỉ dùng một worker vì cache/checkpoint lưu RAM. Giữ model mặc định ở trên.
`requirements.txt` dẫn tới **một lock duy nhất**: `requirements-locked.txt`.
Các recipe FAISS/ví dụ cũ ở `docs/historical_requirements/`, không cài chồng.
Không đưa `.env`, API key hoặc `.venv` vào Git/bài nộp.

## Kiểm tra không gọi dịch vụ

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q -p no:cacheprovider tests
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.smoke_handover
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.check_rag_retrieval --output evidence_recheck
.\.venv\Scripts\python.exe -X utf8 -m benchmarks.verify_final
```

Smoke dùng model/web fixture và PDF thật. Không gọi đây là kết quả Groq/Tavily mới.
Các script live vẫn được giữ để tái lập phép đo, chỉ chạy khi chủ động dùng quota.

## Nội dung code và minh chứng

- `agent.py`, `main.py`, `frontend/`: API `/chatbot` và graph phân nhánh theo luật;
  RAG/web truy xuất rồi kiểm citation/quote. Chưa có agent tự lập kế hoạch.
- `Stress.pdf`, `Rag_tool.py`, `retrieval.py`: BM25 cân bằng mục, tối đa 650 ký tự,
  overlap mục tiêu 180, top-3. Hash PDF và runtime ở `handover/EXPECTED_RUNTIME_IDENTITY.json`.
- `response_cache.py`: exact cache RAM TTL 300 giây, capacity 128. Bộ nhớ phiên
  dùng InMemorySaver; ID caller tự khai không phải cơ chế đăng nhập/phân quyền.
- `math_graph.py`: executor riêng, chưa gắn vào chatbot hoặc LLM tool choice.
- `handover/`: nguyên bản log/trace/context/usage, bộ đề và phiếu người chấm.
- `evidence/`: chat lịch sử, lỗi auth, các lượt kiểm tra có ngày và chỉ mục từng câu.
- `docs/`: bảng phủ, giới hạn, AI Disclosure, chỉ mục bộ đề và nhật ký thay đổi.
- `labs/`: bài tập độc lập có starter/solution; gói lab được phát riêng khi nộp.

RAG thật: 5 hồi quy + 8 câu mới ngày 28/10; 13 phiếu đạt tổng **96/104**.
Web thật: 4 câu kỹ thuật, **2 trả lời/2 từ chối**, điểm người dùng **20/32**.
Một người chấm; web có Codex hỗ trợ, chưa thẩm định URL độc lập. Không quy các điểm
này thành độ chính xác hay hiệu quả lâm sàng. HTTP 200, quote khớp và retrieval có
đủ span là ba minh chứng riêng, không tự chứng minh đáp án đúng.

Các README/metadata trong thư mục bằng chứng là ghi chú tại thời điểm xuất; giữ
nguyên cả lỗi, từ chối và trạng thái trước push. Nhật ký bản cuối ở `docs/JOURNAL.md`.
Word/notebook cũ, ảnh sinh báo cáo và launcher CLI không thuộc demo đã được loại
khỏi cây nộp; vẫn còn trong lịch sử Git. Báo cáo được nộp riêng cùng code.
