import logging
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import Agent

load_dotenv()

app = FastAPI(title="Chatbot ho tro tam ly - Demo API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageIn(BaseModel):
    question: str


class MessageOut(BaseModel):
    response: str


def get_final_answer(result: dict[str, Any]) -> str:
    messages = result.get("messages", [])
    if not messages:
        return "Khong co cau tra loi."

    content = getattr(messages[-1], "content", "")
    if isinstance(content, str):
        return content
    return str(content)


agent: Any = Agent().create_agent()


@app.post("/chatbot", response_model=MessageOut)
async def chatbot_reply(msg: MessageIn):
    try:
        result = agent.invoke({"messages": [("user", msg.question)]})
        return MessageOut(response=get_final_answer(result))
    except Exception:
        logger.exception("Loi tai endpoint /chatbot")
        return MessageOut(
            response="Xin loi, da xay ra loi khi xu ly hoi thoai. Vui long thu lai."
        )


# Chay API:
# uvicorn main:app --reload
