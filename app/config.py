"""Configurações da aplicação, lidas de variáveis de ambiente ou do arquivo .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Partidas — Gestão de Futebol Suíço"
    database_url: str = "postgresql+psycopg://partidas:partidas@localhost:5432/partidas"
    secret_key: str = "troque-esta-chave-em-producao"
    timezone: str = "America/Sao_Paulo"
    debug: bool = False
    # Em produção (atrás de HTTPS) deixe True para o cookie de sessão só trafegar com criptografia.
    cookie_seguro: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
