from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://user:password@db:5432/lu_estilo_db"
    
    SECRET_KEY: str = "sua_chave_secreta_muito_segura_aqui_e_troque_em_producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SENTRY_DSN: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings():
    return Settings()