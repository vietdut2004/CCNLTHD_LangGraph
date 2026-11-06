import unittest

import httpx
from groq import APIConnectionError, APITimeoutError
from langgraph.checkpoint.memory import InMemorySaver

from agent import Agent


class FailingModel:
    def __init__(self, error):
        self.error = error

    async def ainvoke(self, messages):
        raise self.error


class ProviderFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_connection_failure_preserves_input_without_fake_answer(self):
        request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        graph = Agent(model=FailingModel(APIConnectionError(request=request)), tools=[]).create_agent(
            InMemorySaver()
        )
        config = {"configurable": {"thread_id": "connection-error-test"}}

        with self.assertRaises(APIConnectionError):
            await graph.ainvoke({"messages": [("user", "Xin chào")]}, config)

        state = await graph.aget_state(config)
        self.assertEqual([m.type for m in state.values["messages"]], ["human"])
        self.assertEqual(state.values["messages"][0].content, "Xin chào")

    async def test_timeout_remains_a_failed_run(self):
        request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        graph = Agent(model=FailingModel(APITimeoutError(request=request)), tools=[]).create_agent()

        with self.assertRaises(APITimeoutError):
            await graph.ainvoke({"messages": [("user", "Xin chào")]})


if __name__ == "__main__":
    unittest.main()
