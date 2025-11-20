import os
from typing import Literal

class Settings:
    ENV: Literal["dev", "prod"] = os.getenv("ENV", "dev").lower()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MOCK_LLM: bool = os.getenv("MOCK_LLM", "true").lower() in ("true", "1", "yes")
    KB_PATH: str = os.getenv("KB_PATH", "")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "30"))
    
    QUERY_MATCH_CONFIDENCE_THRESHOLD: float = float(os.getenv("QUERY_MATCH_CONFIDENCE_THRESHOLD", "0.5"))

settings = Settings()
