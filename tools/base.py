"""
tools/base.py - Centralized Registry of Cardinal's tools

When a new tool is added (file_manager, code_executor, ecc)
needs to be imported here and added to the ALL_TOOLS variable. the Agent will find it automatically
"""

from langchain_core.tools import BaseTool

# tools import
from tools.web_search import web_search
from tools.time_tool import get_current_time

ALL_TOOLS: list[BaseTool] = [
    web_search,
    get_current_time,
    # NOTE: add here new tools found
]

def get_tools(names: list[str] | None = None) -> list[BaseTool]:
    """
    Gets all the registered tools, or a subgroup defined by the name passed as parameter

    Example:
        get_tools()                              # all the tools
        get_tools(["tavily_search_result_json"]) # only the web search tool
    """

    result: list[BaseTool] = []

    if names is not None:
        result = [tool for tool in ALL_TOOLS if tool.name in names]
    else:
        result = ALL_TOOLS
    # #endif

    return result
# #enddef get_tools
