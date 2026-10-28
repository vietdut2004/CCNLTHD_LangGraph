# Khi nào dùng LangGraph qua trải nghiệm triển khai

| Tình huống | Cách phù hợp | Căn cứ và giới hạn |
|---|---|---|
| Chat/RAG/web có từ chối, cache và phiên | StateGraph với node/cạnh điều kiện | Dễ đặt trace ở ranh giới nhánh, fault injection và xem lịch sử; bản bàn giao đã test luồng nhưng chưa so tốc độ với code trực tiếp. Router hiện dùng luật. |
| Hỏi đáp một lượt, gọi một model | Hàm/API trực tiếp | Không có nhánh hay state cần quản lý; thêm graph tăng cấu hình và phụ thuộc. Không có benchmark định lượng so sánh hai cách. |
| RAG tuyến tính retrieve rồi generate, không phiên/cache/nhánh | Pipeline Python đơn giản | Ít trạng thái chuyển tiếp; graph chưa đem lại lợi ích tương xứng. LangGraph hữu ích khi cần thêm vòng kiểm chứng hoặc điều phối nhiều bước, nhưng bản này không chứng minh agent tự lập kế hoạch. |

Vướng mắc thực tế là phiên bản phụ thuộc, trace/identity giữa source và demo, chunk retrieval và grounding. Graph tổ chức luồng không tự giải quyết chất lượng nguồn hoặc độ liên quan của câu trả lời. Ưu tiên sửa ít lỗi có bằng chứng và chấm người thật trước khi thêm tool/model.
