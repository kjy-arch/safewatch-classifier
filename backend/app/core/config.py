from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_SECRET_KEY: str
    GEMINI_API_KEY: str
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
