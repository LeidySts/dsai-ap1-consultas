from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ErroDominio(Exception):
    status_code = 400

    def __init__(self, mensagem: str, **extra: Any):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.extra = extra


class NaoEncontrado(ErroDominio):
    status_code = 404


class Conflito(ErroDominio):
    status_code = 409


class RegraViolada(ErroDominio):
    status_code = 422


class Proibido(ErroDominio):
    status_code = 403


class NaoAutenticado(ErroDominio):
    status_code = 401


class ContaBloqueada(ErroDominio):
    status_code = 423


async def tratar_erro_dominio(_: Request, exc: ErroDominio) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensagem, **exc.extra})
