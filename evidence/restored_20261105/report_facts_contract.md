# Dữ liệu cần để chốt báo cáo

Script đọc file `report_verified_facts.json` trong cùng thư mục. File này chưa được tạo tự động từ những kết quả chưa hoàn tất. Các trường sau được hỗ trợ:

| Trường | Nội dung |
| --- | --- |
| `status` | `verified` chỉ khi đã đối chiếu các câu viết với log; trong lúc chờ dùng `draft_pending_final_live_results`. Đây là trạng thái xác minh tài liệu, không phải điểm chất lượng model. |
| `paragraph_overrides` | Đối tượng có khóa là chỉ số đoạn gốc, ví dụ `"1076"`; giá trị là câu văn mới. Dùng để ghi commit/manifest cuối và bổ sung nhận xét kết luận đã có bằng chứng. |
| `new_section_paragraphs` | Mảng câu văn cho mục 13.12. Phần tử đầu là tiêu đề bắt đầu bằng `13.12 `. Phần này chỉ dùng số mới đã xác minh. |
| `evidence_screenshot_path` | Đường dẫn PNG tương đối từ thư mục này, ví dụ `ui_restore/live_conversation_<run>/conversation_actual_full.png`. Nếu được chỉ định mà file không tồn tại, script dừng. |
| `evidence_screenshot_kind` | `live` cho ảnh hội thoại có phản hồi thật; `initial` cho trang khởi tạo. |
| `evidence_screenshot_caption` | Chú thích nêu ngày, lượt chạy, model, trạng thái quan sát được. Với ảnh live không được dùng lại chú thích “trang khởi tạo”. |
| `evidence_trace_ids` | Mảng trace ID của đúng lượt hội thoại trong ảnh. Bắt buộc khi `kind=live`. Không lấy câu tốt của các lượt khác để ghép ảnh hay thống kê. |
| `evidence_run_id` | Tên lượt chạy hoặc thư mục lưu ảnh/log. |
| `evidence_supporting_logs` | Mảng đường dẫn raw requests/responses, báo cáo capture, CSV hoặc trace server của lượt ảnh. |
| `appendix_paragraphs` | Không bắt buộc. Nếu bỏ trống, script dùng phụ lục B đã soạn về quá trình sửa và vai trò của AI. |
| `toc_overrides` | Không cần điền lúc đầu. Sau khi xuất PDF, `report_check_toc.py --apply` đọc số trang in và điền các ô TOC cần sửa. |
| `appendix_toc_page` | Sau khi xuất PDF, helper TOC tự điền số trang in của phụ lục B. |

## Nội dung thực tế cần gửi cho người biên tập

- Commit hoặc manifest cuối; cấu hình FAISS thật. Hiện đã đọc được cấu hình 1.000/180/top-6, PyVi, mean pooling, normalized L2 cùng PDF/hash và revision model từ `faiss_final_production_retrieval/summary.json`.
- Kết quả bộ kiểm thử nhẹ cuối: số pass, skip, log/XML. Không ghi 64/64 hoặc 67/67 nếu thực tế có hai test opt-in bị bỏ qua.
- Lượt giao diện cuối nguyên bộ ba câu: graph, trace, câu hỏi/phản hồi, status/route, source, latency, usage. Giữ các lượt trước có trả lời trực tiếp thay RAG hoặc web từ chối trong nhóm thất bại của phiên bản tương ứng.
- Lượt RAG tám câu cũ, hai câu ngoài nguồn và câu tiếp nối: chế độ gọi, cấu hình, thời điểm, số lỗi kỹ thuật, số từ chối, usage và log gốc. Không gộp latency auto mode có thêm lượt model chọn tool với forced RAG nếu điều kiện khác nhau.
- Những kiểm tra bị OOM/MemoryError được giữ trong hồ sơ, tách khỏi kết quả lần chạy nhẹ hoàn tất; không xóa hoặc đổi thành pass.

Kết quả retrieval 25/25 span là kết quả truy xuất trên bộ đã dùng chọn cấu hình, không phải 25/25 câu trả lời đúng hay tập đánh giá độc lập. Các điểm RAG 96/104, web 20/32 và 57 unit test cũ vẫn thuộc đúng phiên bản/ngày của chúng.

## Các bước nhẹ có thể chạy ngay

```powershell
.\CCNLTHD_LangGraph\.venv\Scripts\python.exe -X utf8 .\phuc_hoi_theo_bao_cao_20261105\report_revise.py
```

Lệnh chỉ dùng thư viện chuẩn, không nạp embedding hay Word. Nó tạo DOCX ứng viên, plan trước/sau và validation. Các file không được tải lên Drive ở bước này.

## Chỉ chạy sau khi root cho dừng API để đủ RAM

1. Dùng `report_render.py` với Python hệ thống có win32com để Word mở ứng viên chỉ đọc, xuất PDF, rồi tự đóng đúng instance vừa tạo.
2. Dùng Python venv chạy `report_check_pdf.py` và `report_check_toc.py --apply`.
3. Chạy lại `report_revise.py`, xuất lại PDF và đối chiếu TOC/ảnh/các trang mới. Ghi lại hash cuối sau lần xuất này.

Không có Word COM còn hoạt động do người biên tập để lại sau các lần xuất trước; mọi lần đã hoàn tất có `Close(0)` và `Quit()` trong `finally`. Không đóng Word của người dùng dựa trên tên tiến trình chung.
