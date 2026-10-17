import os
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_core.tools import ArgsSchema, BaseTool
from pydantic import BaseModel, Field

load_dotenv()

try:
    from langchain_tavily import TavilySearch
except ImportError:
    TavilySearch = None

try:
    from langchain_community.tools.tavily_search import TavilySearchResults
except ImportError:
    TavilySearchResults = None


class SearchWebInput(BaseModel):
    query: str = Field(..., description="Noi dung can tim kiem tren internet")


class SearchWebTool(BaseTool):
    name: str = "search_web"
    description: str = (
        "Dung de tim kiem thong tin chung tu internet nhu phim, cau chuyen truyen cam hung, "
        "tin tuc, hoac thong tin moi."
    )
    args_schema: ArgsSchema | None = SearchWebInput
    tavily_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))

    def _create_tavily_tool(self) -> Any:
        if not self.tavily_api_key:
            raise ValueError("Missing TAVILY_API_KEY in environment or .env file.")

        if TavilySearch is not None:
            return TavilySearch(api_key=self.tavily_api_key, max_results=3)

        if TavilySearchResults is not None:
            return TavilySearchResults(tavily_api_key=self.tavily_api_key, max_results=3)

        raise ImportError(
            "Missing Tavily package. Install langchain-tavily or langchain-community."
        )

    def _format_results(self, results: Any) -> str:
        if isinstance(results, dict):
            items = results.get("results", [])
        elif isinstance(results, list):
            items = results
        else:
            items = []

        if not items:
            return "Khong co ket qua phu hop."

        formatted_results = []
        for item in items[:3]:
            title = item.get("title", "Khong co tieu de")
            content = item.get("content") or item.get("snippet") or "Khong co mo ta"
            url = item.get("url", "")
            formatted_results.append(f"- {title}: {content[:200]}... Nguon: {url}")

        return "Cac ket qua tim duoc:\n" + "\n".join(formatted_results)

    def _run(self, query: str, run_manager=None) -> str:
        try:
            tavily = self._create_tavily_tool()
            return self._format_results(tavily.invoke(query))
        except Exception as exc:
            return f"Loi khi tim kiem: {exc}"
