# Tuần 8 bản chọn evidence v1.3

Bản bàn giao hiện dùng evidence-v1.3-rag-check, không còn dùng trạng thái v1.2 cũ. Hướng dẫn cài/chạy, kết quả mới và giới hạn nằm trong README.md; đối chiếu phiên bản tại handover/EXPECTED_RUNTIME_IDENTITY.json và handover/EVIDENCE_INDEX.json. RAG đã có 13 câu được Huỳnh Lê Sơn chấm, web có bốn câu chấm qua hội thoại có Codex hỗ trợ; không ghi các phiếu này là còn trống hoặc đánh giá độc lập.

Đã tích hợp source vào nhánh cục bộ và kiểm tra 57 unit test, API/frontend và retrieval. Chưa push/merge GitHub hoặc thay demo trên máy nhóm. Kết quả live 28/10 giữ nguyên graph_id của lần đo, tách khỏi smoke fixture và số liệu lịch sử. Các log/ghi chú v1, v1.1, v1.2 trong handover/evidence là mốc lịch sử, không phải phiên bản runtime đang chọn.

Các việc còn lại liên quan triển khai: nhập nhánh trên máy nhóm có quyền, kiểm tra hash/môi trường, chạy demo bằng start_api.py rồi đẩy/merge nhánh theo quy trình nhóm. Không cần đo lại provider chỉ để cập nhật tài liệu. Nếu đo thêm, dùng bộ câu hỏi cố định, lưu raw/usage/trace riêng và chấm trong đúng phạm vi.
