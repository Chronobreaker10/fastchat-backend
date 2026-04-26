from typing import Literal

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    scheme: str = "http"
    host: str = "localhost"
    port: int = 8000


class DatabaseConfig(BaseModel):
    dev_dsn: PostgresDsn
    prod_dsn: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class SecurityConfig(BaseModel):
    secret_key: str
    algorithm: str
    expires_minutes: int = 15
    default_dump: str = "$argon2id$v=19$m=65536,t=3,p=4$dummysalt$dummyhash"


class Settings(BaseSettings):
    database: DatabaseConfig
    security: SecurityConfig
    env: Literal["prod", "dev", "test"]
    default_limit: int = 100
    run_config: RunConfig = RunConfig()
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
    )


settings = Settings()
