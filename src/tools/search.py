#DuckDuckGo for privacy. This tool will be called by the agent whenever the Router or Grader decides the resume isn't enough.
from langchain_community.tools import DuckDuckGoSearchRun

def get_web_search_tool():
    """
    Returns a configured DuckDuckGo search tool.
    """
    return DuckDuckGoSearchRun()

# Usage Example:
# search = get_web_search_tool()
# result = search.invoke("Nishita Sharma IGDTUW projects")