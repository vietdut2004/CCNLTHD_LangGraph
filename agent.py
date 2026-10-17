import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from pydantic import SecretStr

from Rag_tool import RAGTOOL
from searchweb_tool import SearchWebTool

load_dotenv()


class Agent:
    def __init__(self):
        # Keep startup light. RAG builds the vector store only when the tool is used.
        self._rag_tool = RAGTOOL()
        self._searchweb = SearchWebTool()

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("Missing GROQ_API_KEY in environment or .env file.")

        self._llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            temperature=0,
            api_key=SecretStr(groq_api_key),
        )

    def create_agent(self):
        return create_agent(
            model=self._llm,
            tools=[self._rag_tool, self._searchweb],
            system_prompt=(
                "Ban la tro ly tieng Viet. Hay tra loi ngan gon, ro rang. "
                "Dung rag_tool cho cau hoi ve tai lieu noi bo, stress, hoac hit tho. "
                "Dung search_web cho thong tin chung hoac thong tin moi tren internet. "
                "Neu cau hoi lien quan suc khoe tam than nghiem trong, hay khuyen nguoi dung "
                "tim chuyen gia hoac dich vu khan cap tai dia phuong."
            ),
        )
