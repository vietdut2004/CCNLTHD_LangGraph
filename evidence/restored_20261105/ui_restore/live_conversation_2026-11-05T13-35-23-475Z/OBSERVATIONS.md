# Lượt chạy thứ hai — 05/11/2026

Ba câu hỏi được gửi lại trong một phiên mới, sau khi `/health` xác nhận graph `3ad0ff8f1e1c46ee9f5b`, model `openai/gpt-oss-20b`, `fixture:false`. Không dùng lại câu trả lời của lượt trước, không tự retry. Thời điểm bắt đầu các câu: 20:35:31, 20:35:41, 20:35:42 giờ Việt Nam. Nhật ký JSON giữ UTC.

| Câu | Kết quả API | Nhánh | Latency trình duyệt | Input / output token |
|---|---|---|---:|---:|
| Ý nghĩa của hít thở sâu | HTTP 200, `ok` | `rag` | 10.003 s | 3.888 / 1.075 |
| Bạn có khỏe không | HTTP 200, `ok` | `answer` | 1.066 s | 570 / 101 |
| Phim truyền động lực | HTTP 200, `refused`, `INSUFFICIENT_EVIDENCE` | `web` | 11.870 s | 2.678 / 691 |

Câu đầu đã gọi RAG và trả về bốn quote thuộc hai chunk trong `Stress.pdf`, trang 1 và 5. Metadata nguồn ghi Embedding PhoBERT/PyVi, FAISS squared L2, chunk 1000, overlap 180, top-k 6. Câu trả lời ngắn gọn, đúng chủ đề hít thở sâu. Việc có quote và nguồn không thay thế bước thẩm định từng ý trong đáp án.

Câu thứ hai có phản hồi hội thoại. Câu thứ ba vẫn từ chối và trả `sources:[]`, nên chưa tái hiện được danh sách phim trong ảnh báo cáo. Không được ghi cả ba câu là đạt chất lượng hoặc ghép câu trả lời của các lượt khác nhau thành một lượt hoàn chỉnh.

Toàn bộ request và response được lưu trong `requests_responses.json`; `LIVE_RESULTS.csv` được xuất từ đúng dữ liệu đó, token thiếu để trống. Các ảnh `turn_*_actual.png`, `conversation_actual.png`, `conversation_actual_full.png` là ảnh chụp giao diện thật. Ảnh `full` chỉ tăng chiều cao viewport để nhìn đủ hội thoại.

Trace lần lượt: `f513f159610d4debb57d896e76e5ffa7`, `6db3a4c0681640b7a1e9b5b2117851de`, `2b988e97a13d437da68b152e2b80b69b`. Không có điểm người chấm mới. Lượt trước graph `5200e395426bb2a4f7e0` được giữ riêng, nguyên vẹn.
