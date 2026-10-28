from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChangeShield"
    database_url: str = "sqlite:///./changeshield.db"
    max_upload_bytes: int = 2_000_000
    replay_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
