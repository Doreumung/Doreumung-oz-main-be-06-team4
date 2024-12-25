import os
from enum import StrEnum

from pydantic_settings import BaseSettings


class ServerEnv(StrEnum):
    LOCAL = "local"  # 내 로컬 환경
    DEV = "dev"  # 개발 서버
    PROD = "prod"  # 프로덕션 서버


class Settings(BaseSettings):
    database_url: str
    async_database_url: str
    kakao_rest_api_key: str
    kakao_redirect_url: str
    google_client_id: str
    google_client_secret: str
    google_redirect_url: str


def get_settings(env: ServerEnv) -> Settings:
    match env:
        case ServerEnv.DEV:
            return Settings(_env_file="config/.env.dev")  # type: ignore
        case ServerEnv.PROD:
            return Settings(_env_file="config/.env.prod")  # type: ignore
        case _:
            return Settings(_env_file="config/.env.local")  # type: ignore


ENV = os.getenv("ENV", ServerEnv.DEV)
settings = get_settings(env=ENV)  # type: ignore
