# Cài đặt thư viện
# pip install fastapi langserve uvicorn python-dotenv

from fastapi import FastAPI
from langserve import add_routes
from dotenv import load_dotenv
from agent import Agent  # Import Agent hoặc Chain của bạn

#  Khởi tạo agent
agent_instance = Agent()  
agent  = agent_instance.create_agent()
# Khởi tạo FastAPI App
app = FastAPI(
    title="LangServe Agent API",
    version="1.0",
    description="Triển khai Agent Chain qua LangServe",
)

#  Tạo route API tự động cho chain
add_routes(app, agent, path="/chat")
"Tạo ra mặc định 3 endpoint"
"""
POST /chat/invoke → gọi agent đưa ra một câu trả lời trực tiếp với input JSON.
POST /chat/stream → Gọi agent nhưng stream kết quả theo thời gian thực  gọi nhiều input cùng lúc stream đẩy lên liên lục và lấy câu trả lời theo thời gian thực.
/chat/playground → giao diện web test trực tiếp.

"""
# Cách  chạy:
# uvicorn server:app --reload --port 8000
# Sau đó mở: http://localhost:8000/chat/playground
