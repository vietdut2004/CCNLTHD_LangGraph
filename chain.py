from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from pydantic import SecretStr
from typing import Any, cast
import os 
import sys 
from dotenv import load_dotenv 

if hasattr(sys.stdout, "reconfigure"):
    cast(Any, sys.stdout).reconfigure(encoding="utf-8")
    cast(Any, sys.stderr).reconfigure(encoding="utf-8")

# ---  Load .env và Get API Key ---
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.1-8b-instant" 

# ---  Hàm Khởi Tạo Model ---
def initialize_model(api_key: str | None, model_name: str, temp: float = 0.7):
    """
    Khởi tạo và trả về đối tượng ChatGroq.
    Kiểm tra và sử dụng khóa API được truyền vào.
    """
    if not api_key:
        print("LỖI CẤU HÌNH: Khóa GROQ_API_KEY không được tìm thấy.")
        print("Vui lòng đảm bảo file .env tồn tại và khóa API đã được thiết lập.")
        sys.exit(1)

    print(f" Khởi tạo ChatGroq: {model_name}")
    
    # Khởi tạo mô hình bằng cách truyền khóa API và tên model
    llm = ChatGroq(
        model=model_name, 
        temperature=temp,
        api_key=SecretStr(api_key)
    )
    return llm

# ---  Setup Prompt Template ---
system_template = (
    "Bạn là một trợ lý đồng cảm, lắng nghe. Tuy nhiên, bạn không phải là chuyên gia y tế "
    "và phải nhắc người dùng tìm sự giúp đỡ chuyên nghiệp nếu vấn đề nghiêm trọng."
)
human_template = (
    "Cảm xúc hiện tại của tôi là: {user_feeling}. "
    "Tôi muốn nói về chủ đề: {user_topic}. "
    "Hãy lắng nghe và đưa ra lời phản hồi đồng cảm, có trách nhiệm."
)
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_template),
        ("human", human_template),
    ]
)

# ---  Xây dựng và Chạy Chain ---
# Truyền khóa và tên model vào hàm khởi tạo
llm = initialize_model(api_key=GROQ_KEY, model_name=MODEL_NAME)

# Khởi tạo Output Parser
parser = StrOutputParser()

# Xây dựng Chain bằng toán tử | (pipe)
chain = chat_prompt | llm | parser

# Dữ liệu mẫu
input_data = {
    "user_feeling": "căng thẳng",
    "user_topic": "công việc"
}

print("\n--- Chạy Chain Groq.invoke() ---")
print(f"Input: {input_data}")

try:
    response = chain.invoke(input_data)
    print("\n--- Output Chatbot ---")
    print(response)
except Exception as e:
    print(f"\nLỗi khi chạy chain: {e}")
    print("Kiểm tra kết nối mạng hoặc tính hợp lệ của model/API key.")
