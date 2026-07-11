
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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from langchain_ollama import ChatOllama

from config.settings import Settings

logger = logging.getLogger(__name__)
DEFAULT_GEMINI_MODEL: str = "gemini-3.1-flash-lite" # "gemini-1.5-flash"


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
        return False
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

def _build_gemini(s: Settings) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model             = s.gemini_model or DEFAULT_GEMINI_MODEL,
        google_api_key    = s.google_api_key,
        temperature       = s.gemini_temperature,
        max_output_tokens = s.gemini_max_tokens or 4096,
    )
# #enddef _build_gemini

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


    #region    -------------- ONLY GEMINI -------------- #

    if (provider == "gemini"):
        if not settings.google_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=gemini ma GOOGLE_API_KEY non è impostata nel .env"
            )
        # #endif

        model = settings.gemini_model or DEFAULT_GEMINI_MODEL
        logger.info("LLM -> Gemini (%s)", model)
        return _build_gemini(settings)
    # #endif

    #endregion -------------- ONLY GEMINI -------------- #


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

    has_claude = bool(settings.anthropic_api_key)
    has_gemini = bool(settings.google_api_key)
    has_ollama = _ollama_is_running(settings.ollama_base_url)

    available: list[BaseChatModel] = []
    labels   : list[str]           = []

    if has_claude:
        available.append(_build_claude(settings))
        labels.append(f"Claude ({settings.claude_model})")
    # #endif

    if has_gemini:
        available.append(_build_gemini(settings))
        labels.append(f"Gemini ({settings.gemini_model or 'gemini-2.0-flash'})")
    # #endif

    if has_ollama:
        available.append(_build_ollama(settings))
        labels.append(f"Ollama ({settings.ollama_model})")
    # #endif

    if not available:
        raise RuntimeError(
            "Nessun LLM disponibile. Soluzioni:\n"
            "  1) Imposta ANTHROPIC_API_KEY nel .env  (Claude)\n"
            "  2) Imposta GOOGLE_API_KEY nel .env     (Gemini — gratuito)\n"
            "  3) Avvia Ollama: ollama serve && ollama pull llama3.1:8b"
        )
    # #endif

    # if there's only on provider, returns it directly
    if len(available) == 1:
        logger.info("LLM → %s [unico provider disponibile]", labels[0])
        return available[0]
    # #endif

    # otherwise, primary +  fallback chain
    primary   = available[0]
    fallbacks = available[1:]

    # accepts a list and tries in order
    llm = primary.with_fallbacks(
        fallbacks,
        exceptions_to_handle=(
            anthropic.APIConnectionError,
            anthropic.RateLimitError,
            anthropic.APIStatusError,
            ChatGoogleGenerativeAIError,
            Exception,
        ),
    )

    chain_str = " → ".join(labels)
    logger.info("LLM → %s [fallback chain]", chain_str)
    return llm

    # NOTE: this is the old code implementation, is currently just commented because it might be usefull
    # in future implementations or fixes
    # # # has_claude: bool = bool(settings.anthropic_api_key)
    # # # has_gemini: bool = bool(settings.google_api_key)
    # # # has_ollama: bool = _ollama_is_running(settings.ollama_base_url)

    # # # if (has_claude and has_gemini and has_ollama):
    # # #     # Ideal case: Claude as primary with an automatic fallback on
    # # #     # Ollama with LangChain's .with_fallback() catches
    # # #     # the exceptions and re-execute the same
    # # #     # call on the fallback model

    # # #     claude = _build_claude(settings)
    # # #     gemini = _build_gemini(settings)
    # # #     ollama = _build_ollama(settings)

    # # #     # NOTE: update the llm with ollama
    # # #     llm = claude.with_fallback(
    # # #         gemini,
    # # #         exceptions_to_handle=(
    # # #             anthropic.APIConnectionError,
    # # #             anthropic.RateLimitError,
    # # #             anthropic.APIStatusError,
    # # #         ),
    # # #     )
    # # #     logger.info(
    # # #         "LLM → Claude (%s) & Ollama fallback (%s)",
    # # #         settings.claude_model,
    # # #         settings.ollama_model,
    # # #     )

    # # #     return llm
    # # # # #endif

    # # # if (has_claude):
    # # #     logger.info(
    # # #         "LLM → Claude (%s) [Ollama is not available]",
    # # #         settings.claude_model
    # # #     )

    # # #     return _build_claude(settings)
    # # # # #endif

    # # # if (has_gemini):
    # # #     available.append(_build_gemini(settings))
    # # #     labels.append(f"Gemini ({settings.gemini_model or 'gemini-2.0-flash'})")
    # # # # #endif

    # # # if (has_ollama):
    # # #     logger.warning(
    # # #         "LLM → Ollama (%s) [ANTHROPIC_API_KEY not set — using Ollama]",
    # # #         settings.ollama_model,
    # # #     )

    # # #     return _build_ollama(settings)
    # # # # #endif

    # # # raise RuntimeError(
    # # #     "No LLM are available right now. Possible solutions:\n"
    # # #     "- 1) Set the ANTHROPIC_API_KEY key/value inside the .env file\n"
    # # #     "- 2) Start Ollama: 'ollama serve && ollama pull llama3.1:8b'"
    # # # )
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

    def with_tools(self, tools: typing.Sequence[BaseTool]) -> BaseChatModel:
        """
        Returns the LLM with binded tools
        This works with Claude (native function calling) and also with
        Ollama on specific models that supports tool use (llama3.1, mistral-nemo, ecc.).
        """

        return self.llm.bind_tools(list(tools))
    # #enddef with_tools

    def reload(self) -> None:
        """Forces the re-init, usefull if the connection has changed during runtime"""

        self._llm = None
        _ = self.llm
    # #enddef reload
# #endclass LLMBackend
