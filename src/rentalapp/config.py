from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, sourced from environment / .env.

    Every module reads config through this object rather than os.environ
    directly, so new settings (e.g. an S3 bucket for documents, an SMTP
    server for notifications) only need to be added here.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Rental Property Management API"
    environment: str = "development"

    database_url: str = "sqlite:///./rentalapp.db"

    secret_key: str = "change-me-to-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # bcrypt work factor; each +1 doubles hashing time. Tests lower it.
    bcrypt_rounds: int = 12


@lru_cache
def get_settings() -> Settings:
    return Settings()
