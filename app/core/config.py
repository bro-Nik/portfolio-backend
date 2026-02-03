import os


class Settings:
    DB_ECHO: bool = os.getenv('DB_ECHO', 'false').lower() in ('true', '1')
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))
    DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    DB_URL: str = os.getenv('DATABASE_URL', '')

    JWT_SECRET: str = os.getenv('JWT_SECRET', '')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', '')


settings = Settings()
