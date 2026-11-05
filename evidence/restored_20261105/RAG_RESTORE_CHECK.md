# Khôi phục RAG theo source và báo cáo

Ngày kiểm tra: 05/11/2026. Tài liệu nguồn vẫn là `Stress.pdf`, 6 trang, SHA-256 `91c16764898a88f26bb73706d1188afd3e3631f8a462c08fd76130a64ebc736a`.

## Phần đã sửa

RAG của chương trình đã trở lại luồng PDF → chia đoạn → embedding tiếng Việt → FAISS → đưa các đoạn tìm được cho model trả lời. `Rag_tool.py` dùng `faiss_retrieval.py`; không chuyển sang BM25 khi embedding hoặc FAISS gặp lỗi. Lỗi tải model và đọc nguồn được trả về luồng xử lý lỗi của API.

Model embedding giữ đúng tên trong source cũ và báo cáo: `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base`, 768 chiều. Revision được cố định tại `608779b86741a8acd8c8d38132974ff04086b138`. Model đã có trong cache của source làm việc cũ, được sao chép vào `.cache/huggingface` của project. Không thay model, không gọi dịch vụ embedding trả phí. Hash từng file công khai được ghi trong `EMBEDDING_AND_PDF_LOCK.json`.

Hai bổ sung trong bước embedding là tách từ bằng PyVi theo hướng dẫn của tác giả model và chuẩn hóa vector. Vẫn dùng mean pooling của cách gọi `HuggingFaceEmbeddings` ban đầu. Phần mở đầu chỉ tên PDF trong câu hỏi được bỏ trước khi embedding; nội dung câu hỏi được giữ. Runtime không đọc câu hỏi mẫu, đáp án tham chiếu hoặc nhãn chấm.

| Tham số | Bản gốc để đối chiếu | Bản khôi phục được chọn |
|---|---|---|
| Chia đoạn | RecursiveCharacterTextSplitter | RecursiveCharacterTextSplitter |
| Giới hạn mỗi đoạn | 500 ký tự | 1.000 ký tự |
| Overlap | 50 ký tự | 180 ký tự |
| Số đoạn lấy tối đa | 2 | 6 |
| Tách từ trước embedding | Chưa có | PyVi 0.1.1 |
| Chuẩn hóa vector | Không | Có |
| Chỉ mục | FAISS IndexFlatL2 | FAISS IndexFlatL2 |
| Điểm trả về | Khoảng cách L2 bình phương | Khoảng cách L2 bình phương trên vector đã chuẩn hóa |

Khoảng cách nhỏ hơn nghĩa là vector gần hơn. Điểm này không phải xác suất câu trả lời đúng. Thông số chia đoạn của bản mới khác bản cũ; vì vậy kết quả, latency và usage cũ không được gán sang bản khôi phục.

Mỗi đoạn trả về có thứ hạng, số trang bắt đầu từ 1, nội dung nguyên gốc, offset đầu/cuối, tên mục, khoảng cách và định danh nguồn. Việc đọc PDF và băm hash dùng cùng một bản byte để tránh ghi nhận nguồn khác với nội dung đã truy xuất. Có `RAGTOOL.prepare()` để chuẩn bị model/index trước khi phục vụ yêu cầu; hàm này không gọi Groq.

## Đã kiểm tra thực tế

Lượt xác nhận cuối dùng chính `RAGTOOL` của chương trình trên 27 câu đã có. Trong đó 25 câu có đáp án trong PDF và 2 câu ngoài PDF. Các đoạn cần đối chiếu xuất hiện đầy đủ trong kết quả truy xuất của 25/25 câu có đáp án, gồm 8/8 câu cũ. Hai câu ngoài PDF không được tính là trả lời đúng hoặc từ chối đúng chỉ dựa vào retrieval.

PDF tạo ra 12 đoạn, đoạn dài nhất 987 ký tự. Mỗi câu nhận tối đa 6 đoạn; tổng nội dung lớn nhất quan sát được là 5.424 ký tự. Lượt đầu có cả thời gian tải model và chuẩn bị index: 58.061,958 ms. Các câu sau có thời gian retrieval từ 141,857 đến 735,943 ms. Đây là thời gian retrieval cục bộ, chưa phải latency gọi Groq.

Kết quả từng câu, đáp án đối chiếu và toàn bộ đoạn theo thứ hạng được lưu trong:

- `faiss_final_production_retrieval/results.jsonl`
- `faiss_final_production_retrieval/results.csv`
- `faiss_final_production_retrieval/summary.json`
- `faiss_final_production_retrieval.log`

Mã RAG, script kiểm tra, tests và requirements đã được chụp lại trước lần chạy tại `faiss_production_source_snapshot/`. `faiss_final_production_run_identity.json` xác nhận các file này không đổi trong lúc chạy, exit code bằng 0.

Các kiểm tra cơ chế có 10/10 ca đạt và `pip check` không báo thiếu/xung đột thư viện. Tests dùng vector fixture ba chiều để kiểm tra chỉ mục, thứ hạng, offset, cấu hình và đường lỗi; không dùng các tests này làm điểm chất lượng embedding. Lượt retrieval 27 câu dùng model embedding thật trong máy, không dùng fixture và không gọi Groq. Số liệu trả lời thật phải lấy từ các lượt gọi API riêng.

## Những thử nghiệm và lỗi được giữ lại

Bản 500/50/top-2 chưa tách từ được chạy lại thật, không phải số liệu lịch sử: chỉ 6/25 câu đủ các span đối chiếu, trong đó 1/8 câu cũ. Kết quả nằm trong `faiss_retrieval_comparison/`. Những kết quả này được giữ nguyên để thấy rằng chỉ đổi tên backend sang FAISS chưa giải quyết được chất lượng truy xuất.

Cấu hình 650/180/top-4 với PyVi và vector chuẩn hóa đạt 20/25 câu đủ span. Các câu còn thiếu là `rag_08`, `new_01`, `new_05`, `new_06`, `fresh_02`. So sánh chia theo mục và thêm heading không cải thiện đồng đều. Kiểm tra CLS, pooler và trained MLP của checkpoint cũng không cho kết quả tốt hơn mean pooling trong phạm vi đã chạy. Toàn bộ kết quả được giữ ở `faiss_segmented_comparison/`, `faiss_sectioned_comparison/` và `faiss_pooling_comparison/`.

Lần kiểm tra production đầu tiên gặp `TypeError` do truyền sai tên tham số cache của SentenceTransformer. Lỗi đã sửa bằng tham số `cache_folder` đúng với thư viện đang cài; log lỗi vẫn còn tại `faiss_production_retrieval.log`. Trước đó pip không truy cập được mạng trong sandbox; việc cài PyVi đã chạy lại với quyền mạng và hoàn tất. Không tạo kết quả model để bù cho những lần thất bại.

## Giới hạn cần ghi đúng

Bộ 27 câu đã được dùng trong các lần sửa trước và được dùng để chọn thông số lần này. Kết quả 25/25 chỉ cho biết đủ span trong bộ hồi quy; đây không phải đánh giá độc lập và không chứng minh model trả lời đúng 25/25. Không có điểm người thật nào được tự điền.

Đổi từ top-2 sang top-6 làm ngữ cảnh gửi model dài hơn. Đó là đánh đổi để giữ đủ thông tin của các câu hỏi nhiều ý, có thể làm token đầu vào và latency tăng. Không dùng số liệu token/latency cũ để mô tả cấu hình mới. Tokenizer giới hạn 256 token; kiểm tra cả 12 đoạn thực tế cho thấy từ 107 đến 221 token sau tách từ, không đoạn nào vượt giới hạn. Nội dung đoạn đưa vào trả lời và trích dẫn giữ nguyên. Chi tiết nằm trong `EMBEDDING_TOKEN_LENGTH_AUDIT.json`.

`retrieval.py` và các log BM25 cũ chỉ được giữ cho việc tái hiện lịch sử; RAG đang chạy không gọi BM25. Các số liệu FAISS ngày 24/10 và BM25 ngày 28/10 vẫn thuộc đúng phiên bản, ngày chạy và trace gốc của chúng.

## Lệnh tái lập

Chạy từ thư mục project, bằng Python của môi trường đã cài đúng `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests/test_rag_check.py -q
.\.venv\Scripts\python.exe -m benchmarks.check_rag_retrieval --output ..\ket_qua_faiss_moi
```

Thư mục output phải chưa tồn tại để tránh ghi đè log. Máy chưa có cache model cần tải đúng revision công khai nói trên; lần đầu có thể mất thời gian. Cần tách thời gian chuẩn bị index với thời gian xử lý khi index đã sẵn sàng.
