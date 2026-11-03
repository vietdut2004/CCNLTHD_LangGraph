# Kết quả kiểm thử thực tế API demo — dữ liệu cho Chương 13

Thời điểm: 2026-10-20T15:46:06.271154+07:00 đến 2026-10-20T15:46:57.118252+07:00 (UTC+7).
Mã nguồn: `01ad2c014c2e948b8c6a97d875d2573ab2b2838b`. Model: `openai/gpt-oss-20b`, temperature = 0.

## Cách đo

Schema được lấy trực tiếp từ `http://127.0.0.1:8000/openapi.json`. Bản demo `/docs` trả HTTP 200. Các phép đo có token chạy qua HTTP ở `http://127.0.0.1:8001/chatbot`, là cùng `main.app` được thêm callback và middleware trong tiến trình riêng; không sửa mã nghiệp vụ. Schema hai bản được so sánh bằng nhau. Bản ở cổng 8000 được giữ nguyên.

Đo tuần tự (concurrency = 1), một warm-up không tính vào bảng, nghỉ 2 giây giữa các yêu cầu, timeout mỗi yêu cầu 120 giây, công cụ đo không retry. SDK có thể tự retry theo cấu hình mặc định của demo. Latency dùng `perf_counter`, tính từ trước khi gửi POST tới khi nhận toàn bộ phản hồi; bao gồm HTTP, callback, LLM, công cụ và retry nếu có. Không phải time-to-first-token. P50/P95 dùng nearest-rank; mẫu nhỏ nên P95 chỉ mang tính mô tả lần chạy này.

Token lấy từ `AIMessage.usage_metadata` do Groq/LangChain cung cấp cho từng lời gọi model hoàn tất; có giữ thêm token_usage gốc trong log. Cộng tất cả lời gọi, kể cả lời gọi lồng trong RAG nếu được callback ghi nhận. Output token có thể bao gồm reasoning token theo cách tính của nhà cung cấp. Đây không phải phép đếm từ ký tự. Không quy đổi thành chi phí. Lời gọi lỗi không có usage là dữ liệu thiếu; không suy ra tiêu thụ bằng 0.

## Kết quả

| Nhóm | Số yêu cầu | Đạt / lỗi | Tỷ lệ lỗi kỹ thuật | Trung bình (ms) | P50 (ms) | P95 (ms) | Input / output / tổng token quan sát |
|---|---:|---:|---:|---:|---:|---:|---:|
| Hội thoại cơ bản | 10 | 10 / 0 | 0.0% | 754.073 | 705.189 | 1108.563 | 3242 / 1467 / 4709 |
| Đầu vào sai có chủ đích | 3 | 3 / 0 | 0.0% | 29.076 | 14.869 | 58.792 | Không có usage được ghi nhận |

Tổng workload đầu vào hợp lệ, không gồm warm-up và kiểm thử validation: **10 yêu cầu**, **0 lỗi kỹ thuật (0.0%)**. Mean = 754.073 ms; P50 = 705.189 ms; P95 = 1108.563 ms. Các con số tổng hợp gồm cả yêu cầu lỗi; xem `successful_latency_ms` trong summary.json để tách latency thành công.

## Phân loại lỗi và giới hạn

- HTTP 422 cho payload sai có chủ đích là kiểm tra validation đạt, không đưa vào mẫu số lỗi workload hợp lệ.
- HTTP 200 chưa đủ để tính là thành công: demo bắt exception và trả câu xin lỗi với mã 200; công cụ cũng có thể trả chuỗi lỗi cho model.
- Một yêu cầu bị tính lỗi khi sai mã HTTP mong đợi, lỗi truyền tải, trả fallback, callback thấy lỗi model/công cụ, trả câu rỗng, hoặc không gọi công cụ được yêu cầu. Model có thể che lỗi công cụ bằng câu trả lời bình thường; log công cụ vẫn dùng để đánh dấu lỗi.
- Không đánh giá chất lượng nội dung, độ chính xác RAG hay hiệu quả lâm sàng. Bộ mẫu nhỏ, chạy một lần, không kiểm thử tải đồng thời và không đại diện SLA production.
- Khóa Tavily có cấu hình lúc đo: **Không**. Không xuất giá trị khóa.
- Đã chạy 14/14 yêu cầu dự kiến (gồm warm-up). Nếu timeout làm dừng đo, các ca chưa chạy không được điền số liệu.

- Lần đo này chỉ gồm hội thoại và validation. Công cụ bị chặn trước khi thực thi; không gửi nội dung Stress.pdf hoặc truy vấn tìm kiếm ra ngoài. Chưa có số liệu RAG/web; không suy rộng kết quả này cho hai chức năng đó.


## Tệp để gửi ChatGPT

Gửi `openapi.json`, `BAO_CAO_KIEM_THU.md`, `summary.json`, `results.csv` và `results.json`. `http_results.jsonl` là phản hồi HTTP gốc; `server_metrics.jsonl` là usage/công cụ/lỗi theo request_id. `environment.json` ghi phiên bản và SHA-256 mã nguồn. Hai script đi kèm cho phép chạy lại trong thư mục `benchmarks` của project đã cài dependencies. Không có `.env` hay khóa API trong gói xuất.

Có thể yêu cầu ChatGPT: 'Dựa trên các tệp đính kèm, bổ sung Chương 13 với phương pháp đo, bảng latency/token/error, phân biệt validation và lỗi công cụ, nêu giới hạn mẫu nhỏ. Chỉ dùng số liệu log; không tự suy ra token cho lời gọi lỗi hoặc tuyên bố chất lượng lâm sàng.'
