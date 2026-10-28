# Việc số 4 Công cụ toán và định tuyến

Đã kiểm tra trực tiếp source sau các việc RAG/web. Không sửa runtime, model, prompt, guard hoặc kết quả/điểm đã chốt. Không gọi Groq/Tavily hay dịch vụ trả phí.

## Kết luận có căn cứ

1. math_graph.py là đồ thị executor riêng: START → execute → finalize → END. Caller truyền name và arguments; execute gọi StructuredTool add hoặc multiply. Không có LLM chọn công cụ hoặc tạo arguments.
2. Bốn ca đạt: add(5,6)=11.0; multiply(5,6)=30.0; tham số sai trả ValidationError; tràn kết quả trả ArithmeticError. Trace có tool_start, tool_end, final; không có model call. Các trường http_status trong math_executor_raw.json là nhãn của helper Trace.finish, không phải phản hồi HTTP từ /chatbot.
3. classify của chatbot là node theo luật: từ khóa giới hạn phạm vi → mode tường minh → từ khóa RAG → từ khóa web → answer. Chạy 12 probe cho kết quả khớp code hiện có; node classify không gọi LLM. Đây không phải 12/12 đúng ý định ngôn ngữ tự nhiên.
4. Giới hạn được giữ trong bằng chứng: ở auto, “Tìm web tài liệu FastAPI” đi RAG vì “tài liệu” có ưu tiên; “Không tìm web, chỉ chào thôi” vẫn đi web. Không thay code hoặc nhãn bằng kỳ vọng ngữ nghĩa để che hai tình huống này. Bộ probe mô tả luật sau khi đọc source, không phải bộ chấm độc lập.
5. Chatbot không có nhánh add/multiply/math và không gắn đồ thị executor này. Gửi “Tính (2+3)*4” qua TestClient với model fixture đi answer, gọi fixture một lần, không gọi tool toán. Câu trả lời fixture chỉ là nhãn chẩn đoán; không dùng để chấm đáp án 20 hoặc làm kết quả model thật.
6. Mẫu code bind_tools/ToolNode trong báo cáo là minh họa riêng, chưa phải thí nghiệm LLM tool choice. Ảnh OutputParserException cũ không chứng minh tool đã chạy. Giữ phạm vi executor/router, chưa xác nhận agent tự lập kế hoạch hoặc chuỗi add rồi multiply do model điều phối.

## Bằng chứng

- evidence/math_executor_raw.json và math_executor_scope.json: bốn ca executor trong tiến trình, 0 LLM.
- evidence/router_node_cases.json: 12 ca và trace của riêng classify, không gọi provider.
- evidence/chatbot_math_chain_probe.json và chatbot_probe_trace.jsonl: biên tích hợp API dùng fixture, không kiểm chất lượng toán của model.
- evidence/*graph_actual.json/.mmd: xuất từ các đối tượng đồ thị đã compile, thể hiện đồ thị toán và chatbot riêng nhau.
- evidence/source_hashes.json và summary.json: hash source/môi trường lần kiểm tra. Không gán graph_id này vào log live RAG/web cũ.
- relevant_tests.xml: bốn kiểm thử liên quan đã chạy đạt (một test bốn ca toán, ba test nhánh chat/RAG/web bằng fixture). Không gọi đây là một lượt chạy lại toàn bộ 57 unit test.

Không so latency/token fixture với dịch vụ thật. Token 0 chỉ là bằng chứng các ca executor không gọi model, không đại diện chi phí toàn chatbot. Node answer/grounded trong ứng dụng thật vẫn gọi model.

## Báo cáo

Mục 13.5 mô tả executor riêng và router theo luật. Phần minh họa tool calling/ảnh lỗi ở Chương 10 được phân biệt với bằng chứng đo. Dòng Toán trong 13.11 thu hẹp đúng kết luận. Các kết quả/điểm RAG và web giữ nguyên; chưa push hoặc deploy.
