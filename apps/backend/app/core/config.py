"""env 키 한 곳. 키가 들어오는 순간 각 팩토리가 실 어댑터를 고른다(코드 수정 없음)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SARAMIN_API_KEY: str | None = None
    JOBKOREA_API_KEY: str | None = None
    WANTED_API_KEY: str | None = None
    VOYAGE_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # 임베더 명시 선택: "voyage" | "gemini" | "mock". 미지정(None)이면 키 있는 것 자동.
    EMBEDDING_PROVIDER: str | None = None


settings = Settings()
