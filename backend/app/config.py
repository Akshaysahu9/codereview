from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./codereview.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
