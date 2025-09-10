from langchain_tavily import TavilySearch
import os
from dotenv import load_dotenv
load_dotenv()

def create_search_tool():
    """
    Creates a Tavily search tool using the new langchain-tavily package.
    Requires TAVILY_API_KEY to be set in the environment.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set.")

    # TavilySearch reads the API key from env and exposes a Tool-compatible interface
    search_tool = TavilySearch(
        max_results=2,
        description="A search engine useful for finding current information, definitions, or context."
    )
    return search_tool
