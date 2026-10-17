# Và thiết lập biến môi trường:
# setx LANGCHAIN_TRACING_V2 "true"
# setx LANGCHAIN_API_KEY "your_langsmith_api_key"
from langsmith import Client
from langsmith.schemas import Example
#  Định nghĩa bộ test (dataset) - ground truth-data
evaluation_test_set = [
    Example(
        inputs={"question": "Kỹ thuật RAG có ưu điểm gì?"},
        outputs={"ground_truth": "Giúp LLM trả lời dựa trên dữ liệu ngoài, giảm ảo giác (hallucination) và cập nhật kiến thức."},
    ),
    Example(
        inputs={"question": "Giả sử tài liệu nội bộ ghi: 'Năm 2024, AI Agent sẽ là xu hướng lớn.' Hỏi xu hướng AI năm 2024 là gì?"},
        outputs={"ground_truth": "AI Agent sẽ là xu hướng lớn."},
    ),
]
# Khởi tạo LangSmith client
client = Client()
" TRên thực tế mình phải sử dụng một LLM hoặc chain để mình đưa câu trả lời."
# import ragchain thực tế hoặc khởi tạo mẫu.
def rag_chain(inputs: dict):
    q = inputs["question"]
    if "RAG" in q:
        return "Kỹ thuật RAG giúp giảm ảo giác và tận dụng dữ liệu ngoài."
    else:
        return "AI Agent sẽ là xu hướng lớn."
# ---------------------------
# Chạy đánh giá tự động
# ---------------------------
run = client.run_on_dataset(
    dataset_name="RAG_Test_Dataset_Nhom10",
    llm_or_chain_factory=rag_chain,  # Chain hoặc Agent thực tế của bạn
    evaluator_names=["faithfulness", "relevance"],  # Các metric chính
    project_name="Evaluation_Run_Nhom_10",
)
print("✅ Đánh giá đã được gửi lên LangSmith Dashboard!")
print("Xem kết quả tại: https://smith.langchain.com")


