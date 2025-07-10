from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    WEB_SERVER_HOST: str
    WEB_SERVER_PORT: str
    RELOAD: bool
    WEBHOOK_URL: str = "http://localhost:8000"  # По умолчанию HTTP
    FORWARD_URL: str = "http://localhost:8000/send_message"
    # WEBHOOK_URL: str = "http://localhost:8000"  # По умолчанию HTTP
    # FORWARD_URL: str = "https://smarty.example.com/api/messages"

    PORT: int = 8000

    class Config:
        env_file = ".env"


config = Settings()