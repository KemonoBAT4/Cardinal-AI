# Pydantic BaseSettings

import typing
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Cardinal's configuration.
    All the variables are read from the .env file or from the environment
    """

    #region    ------------------------ LLM ------------------------ #

    # - "auto"   -> Claude if "ANTHROPIC_API_KEY" is set, Gemini as fallback
    #               if GOOGLE_API_KEY is set, else Ollama as a second fallback
    # - "claude" -> Uses ONLY Claude (throws an error if the api key is not found)
    # - "gemini" -> Uses ONLY Gemini (throws an error if the api key is not found)
    # - "ollama" -> Uses ONLY the local Ollama model
    llm_provider: typing.Literal["auto", "claude", "gemini", "ollama"] = "auto"

    # Claude
    anthropic_api_key  : str   = ""
    claude_model       : str   = "claude-sonnet-4-6"
    claude_max_tokens  : int   = 4096
    claude_temperature : float = 0.7

    # Gemini
    google_api_key     : str   = ""
    gemini_model       : str   = ""
    gemini_max_tokens  : int   = 0
    gemini_temperature : float = 0.7

    # Ollama
    ollama_base_url    : str   = "http://localhost:11434"
    ollama_model       : str   = "llama3.1:8b"
    ollama_temperature : float = 0.7

    #endregion ------------------------ LLM ------------------------ #


    #region    ------------------------ MEMORY ------------------------ #

    redis_url          : str = "redis://localhost:6379"
    chroma_persist_dir : str = "./data/chroma"
    sqllite_path       : str = "./data/cardinal.db"

    #endregion ------------------------ MEMORY ------------------------ #


    #region    ------------------------ TOOL API KEYS ------------------------ #

    tavily_api_key : str = ""

    #endregion ------------------------ TOOL API KEYS ------------------------ #


    #region    ------------------------ VOICE ------------------------ #

    picovoice_access_key : str                                              = ""
    elevenlabs_api_key   : str                                              = ""
    tts_provider         : typing.Literal["coqui", "elevenlabs", "pyttsx3"] = "coqui"

    #endregion ------------------------ VOICE ------------------------ #

    class Config:
        env_file          : str  = ".env"
        env_file_encoding : str  = "utf-8"
        case_sensitive    : bool = False
        extra             : str  = "ignore"
    # #endclass Config
# #endclass Settings
