"""
utils/helpers.py - Shared Utility functions

All the common operations that repeats in more modules,
"""
from langchain_core.messages import BaseMessage


def extract_text(message: BaseMessage | str) -> str:
    """
    Extracts the text from a LangChain message.

    Different providers returns different types of content.
    - Claude / Ollama -> content is a string
    - Gemini          -> content is a list of blocks [{"type": "text", "text": "..."}]

    Args:
        message: a LangChain message or a string

    Returns:
        The extracted text as a string. An empty string if not found.
    """
    if isinstance(message, str):
        return message
    # #endif

    content = getattr(message, "content", message)

    if isinstance(content, str):
        return content
    # #endif

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
            # #endif
        # #endfor

        return " ".join(parts).strip()
    # #endif

    return str(content)
# #enddef extract_text

def truncate(text: str, max_chars: int = 200, suffix: str = "...") -> str:
    """
    Truncates a long text for logs or previews

    Args:
        text:      text to truncate
        max_chars: max char allowed
        suffix:    suffix added if truncated (default "...")
    """
    if len(text) <= max_chars:
        return text
    # #endif

    return text[:max_chars - len(suffix)] + suffix
# #enddef truncate
