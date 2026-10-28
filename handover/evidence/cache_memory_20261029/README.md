# Việc 5 Cache và bộ nhớ

Đã kiểm tra source evidence-v1.3-rag-check sau việc 3/4. Runtime không sửa; không gọi Groq/Tavily hoặc dịch vụ trả phí. Không gán kết quả fixture vào graph_id của các lần chạy thật.

## Kết quả và giới hạn

- Exact cache RAM chỉ dùng cho RAG khi use_cache=true, có user_id và không có session_id. Câu hỏi được NFKC, casefold và chuẩn hóa khoảng trắng; không tìm tương đồng ngữ nghĩa, không bỏ phủ định. Khóa còn gồm user, phiên bản nguồn, model, prompt. TTL 300 giây, tối đa 128 mục, loại theo LRU; giá trị được sao chép khi put/get. Không lưu MySQL, không bền vững sau restart.
- Bốn ca cache cũ được giữ nguyên trong historical_cache_four_cases.json: miss 2.162,275 ms / 1.561 token; hit 40,615 ms / 0 model call / 0 retrieval call / 0 token; đổi người dùng và thêm phủ định đều miss. Đây là log lịch sử graph 9babf4881af66ca761ce, prompt evidence-v1.1-rag-live. Không gọi đây là phép đo tốc độ của bản retrieval v1.3 hoặc suy ra tỷ lệ tiết kiệm toàn hệ thống.
- Kiểm tra mới có 24 yêu cầu API bằng TestClient và 41 điều kiện đạt, bao gồm các điều kiện phụ kiểm tra context. Đây không phải 41 mẫu ngữ nghĩa độc lập. Bốn unit test liên quan cũng đạt; không tuyên bố đã chạy lại toàn bộ 57 test.
- Cache: hit cùng khóa/câu hỏi chuẩn hóa; miss khi đổi user, câu hỏi phủ định, nguồn, model, prompt; opt-out/ẩn danh/phiên hội thoại không dùng cache. Hết hạn tại đúng 300 giây bằng đồng hồ ảo, kiểm tra LRU và bản sao trả về. Đổi model/prompt trong probe chỉ thay nhãn trong bộ nhớ tiến trình fixture, không thay file runtime.
- Bộ nhớ: cùng cặp ID nhận lịch sử; khác user/session hoặc không có session nhận ngữ cảnh riêng; node answer truyền tối đa 5 tin nhắn (hai cặp user/assistant trước và câu hỏi hiện tại). Node grounded hiện chỉ dùng câu hỏi hiện tại và nguồn, chưa hỗ trợ hỏi tiếp theo lịch sử tài liệu. Checkpointer vẫn giữ State trong RAM, giới hạn 5 tin chỉ là cửa sổ gửi model, không phải giới hạn tổng dung lượng State.
- user_id/session_id là dữ liệu người gọi tự khai. Probe dùng lại cùng ID nhận cache/lịch sử: tách State không xác nhận danh tính hoặc phân quyền. Đây là giới hạn demo; không trình bày như đã bảo vệ dữ liệu giữa người dùng thật.
- Tạo Agent/app mới làm cache và lịch sử trống. Probe này mô phỏng vòng đời bộ nhớ; không phải phép đo restart một dịch vụ triển khai. Đọc code xác nhận chỉ có RAM, không có persistence MySQL.
- FixtureModel chỉ ghi/nhắc số lượng tin nhắn và nội dung chẩn đoán, không chứng minh model thật hiểu/nhớ đúng. Các lượt fixture gọi adapter không có usage nhà cung cấp nên total_tokens=null; chỉ khi không gọi adapter mới ghi 0. Không có điểm người thật hay điểm chất lượng memory mới.

## Chạy lại không cần API key

Cài requirements-week8.txt từ source_snapshots trong môi trường Python tương thích. Đứng ở thư mục chứa gói này:

```bash
python benchmarks/check_cache_memory.py --source source_snapshots --out evidence_recheck
```

Script nhận source làm tham số và tạo bằng chứng mới ở thư mục out; dùng đường dẫn mới để giữ nguyên log bàn giao. Các bản source_snapshots là bản sao byte-for-byte của mã đã nhận, kèm source_hashes.json; dùng cho tái lập, không thay thế việc tích hợp repository ở việc 7.

## Phạm vi sửa báo cáo

Chỉ sửa hai đoạn giới hạn bộ nhớ ứng dụng tại Chương 8; mục 13.6, 13.7; hai dòng Cache/Bộ nhớ trong bảng 13.11. Nội dung Chương 9 đã phân biệt exact RAM với minh họa MySQL/FAISS nên giữ nguyên. Giữ nguyên các phần khác, số liệu RAG/web, điểm người chấm và phần của thành viên khác. So sánh XML xác nhận chỉ các vị trí trên thay đổi. Chương 13 vẫn bốn trang; số trang toàn bản hiện tại không tăng. Không push repository hoặc deploy.
