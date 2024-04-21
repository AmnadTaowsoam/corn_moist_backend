from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    backend_host: str
    backend_port: int
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    user_exist_endpoint: str
    corn_moist_fe_endpoint: str
    app_address: str
    cors_origins:str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
custom_headers = {
    'Origin': settings.app_address  # ใช้ settings.app_address แทนการสร้าง string ใหม่
}

