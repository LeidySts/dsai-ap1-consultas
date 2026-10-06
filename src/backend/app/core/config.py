from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres@localhost:5432/marcaconsulta"
    jwt_secret: str = "dev-apenas-troque-em-producao"
    app_timezone: str = "America/Sao_Paulo"
    frontend_url: str = "http://localhost:5173"
    git_commit: str = ""
    render_git_commit: str = ""
    seed_demo: bool = False

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                return "postgresql+psycopg://" + url[len(prefixo):]
        return url

    @property
    def versao(self) -> str:
        return self.render_git_commit or self.git_commit or "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
