# Nguồn và phạm vi

Stress.pdf SHA256: 91c16764898a88f26bb73706d1188afd3e3631f8a462c08fd76130a64ebc736a. Sáu trang, dùng nguyên văn để kiểm tra retrieval. Bản PDF không có hồ sơ tác giả y khoa đã xác minh.

Bài web có tiêu đề và các mục khớp nội dung: “Các kỹ thuật thở sâu để giảm căng thẳng”, đơn vị xuất bản Vinmec, ngày cập nhật hiển thị 22/07/2024, truy cập 28/10/2026: https://www.vinmec.com/vie/bai-viet/cac-ky-thuat-tho-sau-de-giam-cang-thang-vi . Đây là đối chiếu nội dung, chưa xác minh chuỗi xuất bản của PDF; trang không hiển thị tên tác giả cá nhân. Metadata người xuất PDF không được dùng làm tác giả chuyên môn. Không coi nguồn này là đánh giá chuyên gia cho chatbot.

Tài liệu chính thức, kiểm tra ngày 28/10/2026:
- LangGraph Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- Groq: https://console.groq.com/docs/quickstart
- Tavily Search: https://docs.tavily.com/documentation/api-reference/endpoint/search
- FAISS, dùng lại trong bản khôi phục 05/11: https://github.com/facebookresearch/faiss/wiki
- Model card embedding, cùng checkpoint trong bản gốc và bản khôi phục: https://huggingface.co/VoVanPhuc/sup-SimCSE-VietNamese-phobert-base
- Groq Structured Outputs, kiểm tra 05/11/2026 để dùng JSON Schema strict với model hiện tại: https://console.groq.com/docs/structured-outputs

Bản tuần 8 lịch sử dùng BM25. Bản khôi phục 05/11 dùng lại embedding + FAISS,
revision `608779b86741a8acd8c8d38132974ff04086b138`, PyVi và mean pooling.
Giữ riêng cấu hình/số liệu từng bản; không quy thay đổi kết quả cho riêng một
thuật toán khi đã đổi cả cách chia đoạn, chuẩn hóa và top-k. JSON Schema kiểm
soát cấu trúc phản hồi, không tự xác nhận nội dung trả lời đúng.
