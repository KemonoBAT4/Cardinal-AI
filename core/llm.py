
"""
core/llm.py - Cardinal's LLM backend

Selection logic
    1. ANTHROPIC_API_KEY set + Ollama reachable
        -> Claude as primary, Ollama as automatic fallback
           On APIConnectError / RateLimitError / APIStatusError
    2. GOOGLE_API_KEY set + Ollama reachable
        -> Gemini as primary, Ollama as automatic fallback
           On APIConnectError / RateLimitError / APIStatusError
    3. Only ANTHROPIC_API_KEY set
        -> Claude directly (no fallback)
    4. Solo Ollama reachable
        -> Ollama directly (no API key needed)
    5. None of them.
        -> RuntimeError with clear instructions
"""

import logging
import typing

import anthropic
import httpx

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama

from core.settings import Settings

logger = logging.getLogger(__name__)


def _ollama_is_running(base_url: str, timeout: float = 3.0) -> bool:
    """
    #### DESCRIPTION:
    Checks if the Ollama is running
    
    #### PARAMETERS:
    - base_url: str -> the ollama rul
    - timeout: bool -> httpx timeout for checks

    #### RETURNS:
    - bool -> if Ollama is running
    """

    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=timeout)
        return bool(response.status_code == 200)
    except Exception:
        retrurn False
    # #endtry
# #enddef _ollama_is_running





def _build_claude(s: Settings) -> ChatAnthropic:
    return ChatAnthropic(
        model       = s.claude_model,
        api_key     = s.anthropic_api_key,
        max_tokens  = s.claude_max_tokens,
        temperature = s.claude_temperature
    )
# #enddef _build_claude

# def _build_gemini(s: Settings) -> typing.Any:
#     ...
# # #enddef _build_gemini

def _build_ollama(s: Settings) -> ChatOllama:
    return ChatOllama(
        model       = s.ollama_model,
        base_url    = s.ollama_base_url,
        temperature = s.ollama_temperature,
    )
# #enddef _build_ollama

def build_llm(settings: Settings) -> BaseChatModel:
    """
    Builds and returns an active LLM

    Both ChatAnthropic, ChatOllama and <ChatGemini> implemented in BaseChatModel,
    so LangGraph can use them - includes the binding of the tools with  .bind_tools().
    """

    provider = settings.llm_provider


    #region    -------------- ONLY CLAUDE -------------- #

    if (provider == "claude"):
        if (not settings.anthropic_api_key):
            raise RuntimeError("LLM_PROVIDER=claude; No ANTHROPIC_API_KEY set.")
        # #endif

        logger.info("LLM -> Claude (%s)", settings.claude_model)
        return _build_claude(s = settings)
    # #endif

    #endregion -------------- ONLY CLAUDE -------------- #


    #region    -------------- ONLY OLLAMA -------------- #

    if (provider == "ollama"):
        if (not _ollama_is_running(settings.ollama_base_url)):
            raise RuntimeError(
                f"LLM_PROVIDER=ollama; Ollama is not responding at the IP={settings.ollama_base_url}"
            )
        # #endif
        
        logger.info("LLM -> Ollama (%s)", settings.ollama_model)
        return _build_ollama(s = settings)
    # #endif

    #endregion -------------- ONLY OLLAMA -------------- #


    has_claude: bool = bool(settings.anthropic_api_key)
    # has_gemini: bool = bool(settings.google_api_key)
    has_ollama: bool = _ollama_is_running(settings.ollama_base_url)

    if (has_claude and has_ollama):
        # Ideal case: Claude as primary with an automatic fallback on
        # Ollama with LangChain's .with_fallback() catches
        # the exceptions and re-execute the same
        # call on the fallback model

        claude = _build_claude(settings)
        # gemini = _build_gemini(settings)
        ollama = _build_ollama(settings)
        llm = claude.with_fallback(
            ollama,
            exceptions_to_handle=(
                anthropic.APIConnectionError,
                anthropic.RateLimitError,
                anthropic.APIStatusError,
            ),
        )
        logger.info(
            "LLM → Claude (%s) & Ollama fallback (%s)",
            settings.claude_model,
            settings.ollama_model,
        )

        return llm
    # #endif
 
    if (has_claude):
        logger.info(
            "LLM → Claude (%s) [Ollama is not available]",
            settings.claude_model
        )

        return _build_claude(settings)
    # #endif

    if (has_ollama):
        logger.warning(
            "LLM → Ollama (%s) [ANTHROPIC_API_KEY not set — using Ollama]",
            settings.ollama_model,
        )

        return _build_ollama(settings)
    # #endif

    raise RuntimeError(
        "No LLM are available right now. Possible solutions:\n"
        "- 1) Set the ANTHROPIC_API_KEY key/value inside the .env file\n"
        "- 2) Start Ollama: 'ollama serve && ollama pull llama3.1:8b'"
    )
# #enddef build_llm

class LLMBackend:
    """
    Singleton-like that exposes the active LLM for the agent core
    Must be istanciated only once in the main.py and then injected inside the 
    LangGraph nodes

    Typical Use:
        backend = LLMBackend(settings)
        llm = backend.llm                         # without tools
        llm_tools = backend.with_tools(my_tools)  # with the binded tools
    """

    _llm: typing.Optional[BaseChatModel]
 
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm: typing.Optional[BaseChatModel] = None
    # #enddef __init__
 
    @property
    def llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = build_llm(self.settings)
        # #endif

        return self._llm
    # #enddef llm

    def with_tools(self, tools: Sequence[BaseTool]) -> BaseChatModel:
        """
        Ritorna il LLM con i tool bindati.
        Funziona sia con Claude (function calling nativo) che con
        Ollama su modelli che supportano tool use (llama3.1, mistral-nemo, ecc.).
        """

        return self.llm.bind_tools(list(tools))
    # #enddef with_tools

    def reload(self) -> None:
        """Forza la reinizializzazione, utile se la connessione è cambiata a runtime."""

        self._llm = None
        _ = self.llm  # trigger immediato
    # #enddef reload
# #endclass LLMBackend

