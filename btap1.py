# ==========================================
#  So sánh trạng thái giữa LLM và ChatModel (LangChain + Groq)
# ==========================================

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import SecretStr
import os

# ---  Load .env ---
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise ValueError("Missing GROQ_API_KEY in environment or .env file.")

# -- Khởi tạo model hợp lệ (2025)
MODEL_NAME = "llama-3.1-8b-instant"

# ---  LLM (Stateless) ---
print("=== LLM Stateless ===")

llm = ChatGroq(
    model=MODEL_NAME,
    api_key=SecretStr(groq_key)
)

# Lần 1 — nói tên
res1 = llm.invoke("Tên tôi là An.")
print("Lần 1:", res1.content)

# Lần 2 — hỏi lại
res2 = llm.invoke("Tên tôi là gì?")
print("Lần 2:", res2.content)

# --- Chat Model (Stateful thông qua lịch sử) ---
print("\n=== Chat Model (có state thông qua lịch sử) ===")

chat = ChatGroq(
    model=MODEL_NAME,
    api_key=SecretStr(groq_key)
)
# Lần 1
messages1 = [
    HumanMessage(content="Tên tôi là An.")
]
chat1 = chat.invoke(messages1)
print("Chat Lần 1:", chat1.content)

# Lần 2 — gửi lịch sử vào
messages2 = [
    SystemMessage(content="Bạn là một trợ lý hữu ích."),
    HumanMessage(content="Tên tôi là An."),
    AIMessage(content="Chào An, tôi có thể giúp gì?"),
    HumanMessage(content="Tên tôi là gì?")
]
chat2 = chat.invoke(messages2)
print("Chat Lần 2:", chat2.content)




"""
SystemMessage:yêu cầu cho LLM: LLM có vai trò gì, Hành động Của LLM, Đầu ra mong muốn.
PromptTemplate: Mẫu prompt : LLM có vai trò gì, Hành động Của LLM, Đầu ra mong muốn.
Thằng promptTemplate nó sẽ nhận được input từ người dùng.
"""
