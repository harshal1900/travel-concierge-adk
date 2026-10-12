"""Environment-backed settings. All configuration is read here, never in business logic."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    llm_model: str = "gemini-3.5-flash-lite"
    google_api_key: str = field(default="", repr=False)
    data_provider: str = "mock"
    places_api_key: str = field(default="", repr=False)
    mock_data_dir: str = "data"
    app_env: str = "development"
    service_api_key: str = field(default="", repr=False)
    request_timeout_seconds: int = 45
    rate_limit: str = "30/minute"
    allowed_origins: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_model=os.getenv("LLM_MODEL") or cls.llm_model,
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            data_provider=os.getenv("DATA_PROVIDER") or cls.data_provider,
            places_api_key=os.getenv("PLACES_API_KEY", ""),
            mock_data_dir=os.getenv("MOCK_DATA_DIR") or cls.mock_data_dir,
            app_env=os.getenv("APP_ENV") or cls.app_env,
            service_api_key=os.getenv("SERVICE_API_KEY", ""),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS") or cls.request_timeout_seconds),
            rate_limit=os.getenv("RATE_LIMIT") or cls.rate_limit,
            allowed_origins=_csv(os.getenv("ALLOWED_ORIGINS", "")),
        )


settings = Settings.from_env()
