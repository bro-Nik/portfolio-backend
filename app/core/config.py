from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_url: str = ''
    test_db_url: str = ''

    jwt_secret: str = ''
    jwt_algorithm: str = ''

    redis_url: RedisDsn = 'redis://localhost:6379/0'
    redis_max_connections: int = 20
    redis_timeout: int = 5

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
    )


settings = Settings()
