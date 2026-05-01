from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-this-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+asyncpg://raxus:raxus_pass@localhost:5432/raxus"
    REDIS_URL: str = "redis://:raxus_redis@redis:6379/0"

    VAULT_URL: str = "http://vault:8200"
    VAULT_TOKEN: str = "raxus-vault-token"

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Internal services
    ALERTMANAGER_URL: str = "http://alertmanager:8001"
    INVENTORY_URL: str = "http://inventory:8002"
    NOTIFIER_URL: str = "http://notifier:8003"
    TASKMANAGER_URL: str = "http://taskmanager:8004"
    SLO_URL: str = "http://slo-engine:8005"
    RULES_URL: str = "http://rules-engine:8006"

    class Config:
        env_file = ".env"


settings = Settings()
