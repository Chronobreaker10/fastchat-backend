from typing import Literal

from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiConfig(BaseModel):
    version: str = "1.0.0"
    prefix: str = "/api/v1"
    title: str = "FastChat API"
    description: str = "API для приложения мессенджера Fast Chat"


class CorsConfig(BaseModel):
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:8081",
        ]
    )


class RunConfig(BaseModel):
    scheme: Literal["http", "https"] = "http"
    host: str = "localhost"
    port: int = 8000


class DatabaseConfig(BaseModel):
    dev_dsn: PostgresDsn
    prod_dsn: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0


class SecurityConfig(BaseModel):
    cookie_name: str = "fastchat_access_token"
    secret_key: str
    algorithm: str
    expires_minutes: int = 15


class Settings(BaseSettings):
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    env: Literal["prod", "dev", "test"] = "dev"
    default_limit: int = 10
    cors: CorsConfig = Field(default_factory=CorsConfig)
    run_config: RunConfig = Field(default_factory=RunConfig)
    api_config: ApiConfig = Field(default_factory=ApiConfig)
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
    )


settings = Settings()
