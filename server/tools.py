from __future__ import annotations

import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

# Tavily + LangChain integration
try:  # pragma: no cover
    from langchain_tavily import TavilySearch as _TavilySearch
except Exception as _e:  # pragma: no cover
    _TAVILY_IMPORT_ERROR = _e
    _TavilySearch = None  # type: ignore
else:  # pragma: no cover
    _TAVILY_IMPORT_ERROR = None


class TavilyWebSearchTool:
    """Wrapper around langchain_tavily.TavilySearch with a simple .invoke API.

    Expects `TAVILY_API_KEY` in the environment. Returns a JSON-serializable
    dict when possible, otherwise a string. This keeps compatibility with the
    MCP server's expectations.
    """

    def __init__(self, max_results: int = 5, topic: str = "general") -> None:
        if _TavilySearch is None:
            raise ImportError(
                f"langchain-tavily is required but not available: {_TAVILY_IMPORT_ERROR}. "
                "Install with 'pip install langchain-tavily tavily-python'"
            )
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set.")
        # langchain-tavily reads API key from env internally
        self.tool = _TavilySearch(
            max_results=max_results,
            topic=topic,
            # keep payloads compact by default
            # include_answer=False,
            # include_raw_content=False,
            # include_images=False,
        )

    def invoke(self, input: Dict[str, Any] | str) -> Any:
        if isinstance(input, dict):
            payload = {k: v for k, v in input.items()}
            query = (payload.get("query") or payload.get("input") or "").strip()
        else:
            query = str(input).strip()
            payload = {"query": query}
        if not query:
            raise ValueError("query is required")
        # Pass-through optional args supported at invocation time
        try:
            res = self.tool.invoke(payload)
        except Exception as e:  # surface concise error
            return {"error": f"Tavily search failed: {e}"}
        return res


def create_search_tool() -> TavilyWebSearchTool:
    """Create the Tavily-based web search tool.

    Requires TAVILY_API_KEY and langchain-tavily installed.
    """
    return TavilyWebSearchTool(max_results=5)
