import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from agent import Agent
from main import app
from Rag_tool import RAGTOOL


@tool
def lookup(query: str) -> str:
    """Retrieve a known test document."""
    return "Tài liệu cho: " + query


class FakeModel:
    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        last = messages[-1]
        if isinstance(last, ToolMessage):
            return AIMessage(content="Đã tra cứu: " + last.content)
        if last.content == "lookup":
            return AIMessage(content="", tool_calls=[{
                "name": "lookup", "args": {"query": "hít thở"}, "id": "lookup-1",
            }])
        history = [m.content for m in messages if isinstance(m, HumanMessage)]
        return AIMessage(content=" | ".join(history))


class GraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_result_returns_to_assistant(self):
        graph = Agent(model=FakeModel(), tools=[lookup]).create_agent()
        result = await graph.ainvoke({"messages": [("user", "lookup")]})
        self.assertEqual([m.type for m in result["messages"]], ["human", "ai", "tool", "ai"])
        self.assertEqual(result["messages"][-1].content, "Đã tra cứu: Tài liệu cho: hít thở")

    async def test_thread_memory_and_isolation(self):
        graph = Agent(model=FakeModel(), tools=[]).create_agent(InMemorySaver())
        one = {"configurable": {"thread_id": "one"}}
        two = {"configurable": {"thread_id": "two"}}
        await graph.ainvoke({"messages": [("user", "Tôi là An")]}, one)
        result = await graph.ainvoke({"messages": [("user", "Tên tôi là gì?")]}, one)
        self.assertIn("Tôi là An", result["messages"][-1].content)
        other = await graph.ainvoke({"messages": [("user", "Xin chào")]}, two)
        self.assertEqual(other["messages"][-1].content, "Xin chào")


class RagTests(unittest.TestCase):
    def test_graph_passes_retrieved_text_and_page_to_model(self):
        class Retriever:
            def invoke(self, query):
                return [Document(page_content="Đoạn tài liệu thử nghiệm", metadata={"page": 4})]

        class Model:
            def invoke(self, messages):
                self_received.append(messages[-1].content)
                return AIMessage(content="Câu trả lời từ tài liệu (Stress.pdf, trang 5).")

        self_received = []
        rag = RAGTOOL()
        with patch.object(RAGTOOL, "_get_retriever", return_value=Retriever()), \
             patch("langchain_groq.ChatGroq", return_value=Model()), \
             patch.dict("os.environ", {"GROQ_API_KEY": "test-only"}):
            result = rag.invoke({"query": "Câu hỏi thử nghiệm"})
        self.assertIn("trang 5", result)
        self.assertIn("Đoạn tài liệu thử nghiệm", self_received[0])
        self.assertIn("Câu hỏi thử nghiệm", self_received[0])

    def test_tool_error_does_not_expose_provider_secrets(self):
        with patch.object(RAGTOOL, "_get_retriever", side_effect=RuntimeError("secret-value")):
            result = RAGTOOL().invoke({"query": "stress"})
        self.assertNotIn("secret-value", result)
        self.assertIn("chưa thể tra cứu", result)


class FrontendTests(unittest.TestCase):
    def test_page_and_assets_are_served(self):
        with TestClient(app) as client:
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertIn('lang="vi"', page.text)
            for asset in ("app.js", "style.css", "logo.svg"):
                self.assertEqual(client.get("/static/" + asset).status_code, 200)


if __name__ == "__main__":
    unittest.main()
