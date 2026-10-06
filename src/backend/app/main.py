from fastapi import FastAPI

from app.core.erros import ErroDominio, tratar_erro_dominio
from app.health.router import router as health_router


def criar_app() -> FastAPI:
    app = FastAPI(title="MarcaConsulta")
    app.add_exception_handler(ErroDominio, tratar_erro_dominio)
    app.include_router(health_router, prefix="/api")
    return app


app = criar_app()
