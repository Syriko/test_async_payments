from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = 'zzz500zzz'
    POSTGRES_DB: str = 'test_payments'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432

    # RabbitMQ
    RABBITMQ_HOST: str = 'localhost'
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = 'guest'
    RABBITMQ_PASSWORD: str = 'guest'

    # API
    API_KEY: str = 'secret_api_key'

    # Webhook
    WEBHOOK_RETRY_COUNT: int = 3
    WEBHOOK_TIMEOUT: int = 10

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True
    )

    @property
    def DATABASE_URL(self):
        # return (
        #     f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
        #     f'@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        # )
        return 'postgresql+asyncpg://postgres:zzz500zzz@localhost:5432/test_payments'


    @property
    def RABBITMQ_URL(self):
        return (
            f'amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}'
            f'@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/'
        )


settings = Settings()