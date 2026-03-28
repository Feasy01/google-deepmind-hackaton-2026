from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "DeepMind Hackathon API"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    GOOGLE_API_KEY: str = ""
    VAPI_API_KEY: str = ""
    VAPI_PHONE_NUMBER_ID: str = ""

    DATABASE_URL: str = "postgresql://admin:hackathonpassword@192.168.10.191:5432/vectordb"

    MEDIA_DIR: str = "./assets"
    VAPI_WEBHOOK_URL: str = ""  # Public URL for Vapi to reach backend (ngrok in dev)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
