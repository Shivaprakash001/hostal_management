from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "gemma2-9b-it")
    hms_api_base: str = os.getenv("HMS_API_BASE", "http://localhost:8000")


    # timeouts/retries
    http_timeout: float = float(os.getenv("HTTP_TIMEOUT", 20))
    http_retries: int = int(os.getenv("HTTP_RETRIES", 2))


settings = Settings()