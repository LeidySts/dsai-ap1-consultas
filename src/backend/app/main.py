from fastapi import FastAPI

from app.agenda.router import publico as agenda_publico
from app.agenda.router import router as agenda_router
from app.auth.router import router as auth_router
from app.clinicas.router import router as clinicas_router
from app.core.erros import ErroDominio, tratar_erro_dominio
from app.health.router import router as health_router


def criar_app() -> FastAPI:
    app = FastAPI(title="MarcaConsulta")
    app.add_exception_handler(ErroDominio, tratar_erro_dominio)
    for router in (health_router, auth_router, clinicas_router, agenda_router, agenda_publico):
        app.include_router(router, prefix="/api")
    return app


app = criar_app()
