# Phạm vi và giới hạn của bản nộp

1. **Nguồn và phiên bản.** Runtime đã đo giữ nguyên byte của bản
   `60b2a03`, model `openai/gpt-oss-20b`, graph ID đã đo
   `beebab186d50bedb4180`. Commit nộp có thêm thay đổi hồ sơ và cách đóng gói.
   Trạng thái Git, hash và môi trường phải đọc theo mốc kiểm tra cụ thể; một lần
   push không chứng minh demo đã triển khai trên máy khác.

2. **PDF.** `Stress.pdf` gồm sáu trang, SHA256
   `91c16764898a88f26bb73706d1188afd3e3631f8a462c08fd76130a64ebc736a`.
   Hash xác nhận byte, không xác nhận thẩm quyền y khoa. Chưa xác minh đầy đủ
   chuỗi xuất bản của PDF hoặc tác giả chuyên môn. Xem `SOURCE_REGISTER.md`.

3. **Retrieval.** BM25 cân bằng mục dùng chunk tối đa 650 ký tự, overlap mục tiêu
   180 và top-k 3. Trong 27 câu kiểm tra, 25 câu có đáp án đều truy xuất đủ các
   span yêu cầu; hai câu ngoài PDF không được đưa vào mẫu số coverage. Đây là
   kiểm tra tìm đoạn, không phải kết luận model trả lời đúng 25/25. Điểm BM25
   không phải xác suất hoặc độ tin cậy của đáp án.

4. **RAG thật.** Giữ riêng 5 câu hồi quy và 8 câu mới của ngày 28/10. Bộ tám câu
   có 6 phản hồi trả lời và 2 từ chối với câu ngoài nguồn; bộ này nay là hồi quy.
   Cùng PDF được dùng để xây dựng tham chiếu và đánh giá nên chưa có bộ dữ liệu
   độc lập. Hai lượt lỗi xác thực HTTP 502 và các câu chưa thực hiện vẫn được giữ.
   Không có đáp án model thật để chấm cho những lần gọi thất bại đó.

5. **Lượt lịch sử.** Chat 20/10 dùng nguồn cũ `01ad2c0`; RAG/web 24/10 có graph
   ID và cấu hình khác, trong đó RAG dùng FAISS, chunk 500, overlap 50, top-k 2.
   Không gộp các lượt này với BM25 ngày 28/10 hoặc thay log thất bại bằng kết quả
   của lượt khác. Raw chat 20/10 có trong `evidence/historical/chat_20261020/`.

6. **Web.** Bộ bốn câu chỉ hỏi tài liệu kỹ thuật. Ngày 28/10, web_03 và web_04 trả
   lời; web_01 và web_02 từ chối vì quote không khớp context. Bản nháp model
   không phải phản hồi cuối của API. Mười hai nguồn có thời điểm quan sát khi truy
   xuất; thời điểm đó không phải ngày xuất bản. Lượt 24/10 thiếu thời điểm riêng
   của từng URL, được giữ thiếu. Chưa có thẩm định độc lập từng URL.

7. **Usage và latency.** Thiếu usage được ghi `null` trong JSON và trống trong
   CSV dẫn xuất. Một số raw lỗi cũ ghi observed bằng 0 do thiếu metadata; không
   diễn giải thành đã tiêu thụ hoặc bị tính phí 0 token. Latency HTTP của yêu cầu
   đầu trong hai lượt RAG 28/10 bao gồm kết nối lạnh và chuẩn bị PDF; không trừ
   thời gian này sau khi đo. Không gộp latency của API, graph lab và fixture.

8. **Cache và memory.** Exact cache nằm trong RAM, TTL 300 giây, capacity 128;
   không phải semantic cache. Kiểm tra ranh giới dùng fixture và đồng hồ ảo.
   `InMemorySaver` mất dữ liệu khi restart; ID do caller khai chỉ tách namespace,
   không phải đăng nhập hoặc phân quyền. Chưa đo model thật nhớ đúng và chưa có
   MySQL. Grounded RAG/web hiện không dùng lịch sử hội thoại.

9. **Toán và router.** Bốn ca executor và 12 probe chỉ kiểm tra executor riêng và
   router theo luật. Giữ cả lỗi kiểu dữ liệu, tràn số và hai giới hạn ngữ nghĩa.
   Chatbot chưa nối executor toán; chưa có LLM chọn tool, lập kế hoạch hoặc
   multi-agent.

10. **Kiểm thử kỹ thuật.** Ngày 03/11 đã chạy đạt 57 unit test trong 10,50 giây,
    7 ca trong tiến trình và 4 ca TCP dùng fixture/offline. Strict xác nhận 9
    file runtime, 154 file minh chứng và môi trường khớp. Retrieval đủ span ở
    25/25 câu có đáp án; 2 câu ngoài PDF không chấm coverage. Solution lab đạt
    ba nhánh, một lỗi chủ động và bộ đếm phiên 1–2–1. GET `/`, `/docs`, `/health`,
    `/openapi.json` của `main:app` không fixture đều trả HTTP 200; không có key,
    không POST chatbot, không gọi provider. Log mới nằm riêng trong
    `evidence/verification/final_20261103/`. Các kiểm tra này không thay thế
    đánh giá nội dung provider hoặc thử tải dài hạn; log 29/10 vẫn giữ mốc gốc.

11. **Người chấm.** Điểm RAG 96/104 và web 20/32 đến từ một thành viên có hỗ trợ
    rubric và ghi chép của Codex. Chưa có chuyên gia, người chấm độc lập hoặc
    đồng thuận nhiều người. Không coi tổng rubric là độ chính xác hay hiệu quả
    hỗ trợ tâm lý.

12. **Báo cáo và lab.** Hai lệch trong snapshot báo cáo 29/10 đã được bản báo cáo
    tải ngày 03/11 mô tả đúng: UI chưa có follow-up; latency RAG đầu có chuẩn bị
    PDF. Việc sửa mô tả không bổ sung tính năng hoặc đổi số đo. Lab phát riêng,
    starter có TODO theo đề; `RuntimeError` chủ động là ca lỗi mong đợi. Phần lab
    cốt lõi không gọi LLM nên token bằng 0 khi đã xác nhận không gọi model.
