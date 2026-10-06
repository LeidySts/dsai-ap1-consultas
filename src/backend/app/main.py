from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from app.agenda.router import publico as agenda_publico
from app.agenda.router import router as agenda_router
from app.agendamento.router import router as agendamento_router
from app.auth.router import router as auth_router
from app.busca.router import router as busca_router
from app.clinicas.router import router as clinicas_router
from app.core.erros import ErroDominio, tratar_erro_dominio
from app.health.router import router as health_router

ROUTERS = (
    health_router,
    auth_router,
    clinicas_router,
    agenda_router,
    agenda_publico,
    busca_router,
    agendamento_router,
)
# build do frontend copiado pelo Dockerfile
PASTA_ESTATICOS = Path(__file__).parent / "static"


def servir_frontend(app: FastAPI, pasta: Path) -> None:
    """Serve o build do React; qualquer rota fora de /api cai no index.html (SPA)."""
    raiz = pasta.resolve()

    @app.get("/{caminho:path}", include_in_schema=False)
    def frontend(caminho: str):
        if caminho == "api" or caminho.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Rota não encontrada."})
        arquivo = (raiz / caminho).resolve()
        if caminho and arquivo.is_file() and arquivo.is_relative_to(raiz):
            return FileResponse(arquivo)
        return FileResponse(raiz / "index.html")


def criar_app(pasta_estaticos: Path = PASTA_ESTATICOS) -> FastAPI:
    app = FastAPI(title="MarcaConsulta")
    app.add_exception_handler(ErroDominio, tratar_erro_dominio)
    for router in ROUTERS:
        app.include_router(router, prefix="/api")
    if (pasta_estaticos / "index.html").is_file():
        servir_frontend(app, pasta_estaticos)
    return app


app = criar_app()
