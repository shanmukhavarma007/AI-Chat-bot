from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    NVIDIA_API_KEY: str
    NIM_MODEL: str = "z-ai/glm4.7"
    NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    MAX_HISTORY_PAIRS: int = 10
    SESSION_TIMEOUT_MINUTES: int = 30
    DEFAULT_ENABLE_THINKING: bool = True
    REQUEST_TIMEOUT_SECONDS: int = 120
    TELEGRAM_BOT_TOKEN: Optional[str] = None


settings = Settings()