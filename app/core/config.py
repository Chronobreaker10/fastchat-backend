from functools import cached_property
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEYS_DIR = BASE_DIR / "secret_keys"

Path(SECRET_KEYS_DIR).mkdir(
    parents=True,
    exist_ok=True,
)


class ApiConfig(BaseModel):
    version: str = "1.0.0"
    prefix: str = "/v1"
    title: str = "FastChat API"
    description: str = "API для приложения мессенджера Fast Chat"


class CorsConfig(BaseModel):
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            # "http://localhost:8080",
            # "http://localhost:8081",
            # "http://localhost:80",
            # "https://localhost",
            "http://fastchat_proxy:80",
            "https://fastchat_proxy:443",
        ]
    )


class RunConfig(BaseModel):
    scheme: Literal["http", "https"]
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


class ChatBrokerConfig(BaseModel):
    broadcast_channel_key: str = "chat-events"
    online_users_prefix: str = "chat-online-users"
    user_connections_prefix: str = "user-connections"
    closed_connections_key: str = "closed-connections"


class KafkaConfig(BaseModel):
    bootstrap_server: str = "localhost:9092"
    notifications_topic: str = "notifications"

    @property
    def bootstrap_servers(self) -> list[str]:
        return [self.bootstrap_server]


class SecurityConfig(BaseModel):
    access_token_cookie_name: str = "fastchat_access_token"
    refresh_token_cookie_name: str = "fastchat_refresh_token"
    algorithm: str
    access_token_expires_seconds: int = 15 * 60
    refresh_token_expires_seconds: int = 30 * 24 * 60 * 60
    user_session_store_prefix: str = "fastchat-user-session"
    refresh_token_store_prefix: str = "fastchat-refresh-token"
    encryption_key: str

    @cached_property
    def private_key(self) -> str:
        with Path.open(SECRET_KEYS_DIR / "private.pem") as file:
            return file.read()

    @cached_property
    def public_key(self) -> str:
        with Path.open(SECRET_KEYS_DIR / "public.pem") as file:
            return file.read()


class Settings(BaseSettings):
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    env: Literal["prod", "dev", "test"] = "dev"
    default_limit: int = 10
    websockets_limit_per_user: int = 20
    cors: CorsConfig = Field(default_factory=CorsConfig)
    run_config: RunConfig
    api_config: ApiConfig = Field(default_factory=ApiConfig)
    chat_broker_config: ChatBrokerConfig = Field(default_factory=ChatBrokerConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
    )


settings = Settings()
