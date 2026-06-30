from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ADMIN_USER: str
    ADMIN_PASSWORD: str
    API_KEY: str
    SECRET_KEY: str
    DB_PATH: str = "/app/data/db.sqlite3"
    APK_MAX_SIZE_MB: int = 500
    APK_STORAGE_PATH: str = "/app/data/apks"
    ICON_STORAGE_PATH: str = "/app/data/icons"
    SESSION_MAX_AGE_SECONDS: int = 7 * 24 * 60 * 60  # 7 Tage

    class Config:
        env_file = ".env"


settings = Settings()
