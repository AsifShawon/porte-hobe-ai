from __future__ import annotations

import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

# We use Google Generative AI with the GoogleSearch tool, mirroring web_crawler.py
try:
    from google import genai
    from google.genai import types
except Exception as e:  # pragma: no cover
    genai = None
    types = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


class GoogleWebSearchTool:
    """Minimal Tool-like wrapper exposing an invoke({"query": str}) method.

    Uses Gemini with the GoogleSearch tool enabled to fetch current information
    and return a concise markdown summary with links.
    """

    def __init__(self, model: str = "gemini-2.5-flash", max_results: int = 5) -> None:
        if genai is None or types is None:
            raise ImportError(
                f"google-genai is required but not available: {_IMPORT_ERROR}. Install with 'pip install google-genai'"
            )
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_results = max_results

    def invoke(self, input: Dict[str, Any] | str) -> str:
        if isinstance(input, dict):
            query = (input.get("query") or input.get("input") or "").strip()
        else:
            query = str(input).strip()
        if not query:
            raise ValueError("query is required")

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            "You are a web research assistant. Use Google Search tool to find up-to-date sources.\n"
                            f"Query: {query}\n\n"
                            f"Return up to {self.max_results} high-quality results as markdown bullets with: title, URL, and a 1-2 sentence summary."
                        )
                    )
                ],
            )
        ]
        tools = [types.Tool(googleSearch=types.GoogleSearch())]
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            tools=tools,
        )

        # Non-streaming call to capture full result text
        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            text = getattr(resp, "text", None)
            if text:
                return text
            # Fallback to assembling from parts
            try:
                parts = getattr(resp, "candidates", [])[0].content.parts  # type: ignore[attr-defined]
                return "".join(getattr(p, "text", "") for p in parts)
            except Exception:
                return str(resp)
        except Exception as e:
            return f"[Search Error] {e}"


def create_search_tool() -> GoogleWebSearchTool:
    """Create the Google-based web search tool.

    Requires GEMINI_API_KEY in environment and google-genai installed.
    """
    return GoogleWebSearchTool(max_results=5)
