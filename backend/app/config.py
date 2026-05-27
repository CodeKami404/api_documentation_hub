from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/apihub"
    SECRET_KEY: str = "super-secret-key-change-in-prod"

    class Config:
        env_file = ".env"

settings = Settings()