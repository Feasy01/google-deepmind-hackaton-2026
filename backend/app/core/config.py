from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "DeepMind Hackathon API"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    GOOGLE_API_KEY: str = ""
    HOST_IP: str = "192.168.10.191"
    QDRANT_URL: str = "http://192.168.10.191:6333"

    MEDIA_DIR: str = "./assets"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
