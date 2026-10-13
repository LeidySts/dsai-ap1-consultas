import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp"))

import servidor  # noqa: E402


class ApiFalsa:
    """Simula a API do MarcaConsulta: rotas -> (status, corpo), registrando cada pedido."""

    def __init__(self):
        self.rotas: dict[tuple[str, str], list] = {}
        self.pedidos: list[httpx.Request] = []
        self.tokens_validos = {"token-1"}
        self.logins = 0

    def responder(self, metodo: str, caminho: str, *respostas):
        self.rotas[(metodo, caminho)] = list(respostas)

    def __call__(self, pedido: httpx.Request) -> httpx.Response:
        self.pedidos.append(pedido)
        caminho = pedido.url.path.removeprefix("/api")
        if caminho == "/auth/login":
            self.logins += 1
            corpo = json.loads(pedido.content)
            if corpo != {"email": "paciente@teste.com", "senha": "segredo"}:
                return httpx.Response(401, json={"detail": "E-mail ou senha inválidos."})
            return httpx.Response(200, json={"access_token": f"token-{self.logins}", "refresh_token": "r"})
        if caminho.startswith("/consultas"):
            token = pedido.headers.get("Authorization", "").removeprefix("Bearer ")
            if token not in self.tokens_validos:
                return httpx.Response(401, json={"detail": "Sessão expirada."})
        respostas = self.rotas[(pedido.method, caminho)]
        status, corpo = respostas.pop(0) if len(respostas) > 1 else respostas[0]
        return httpx.Response(status, json=corpo)


@pytest.fixture
def api_falsa(monkeypatch):
    falsa = ApiFalsa()
    cliente = servidor.ClienteAPI(
        "https://exemplo.test/api", "paciente@teste.com", "segredo", transport=httpx.MockTransport(falsa)
    )
    monkeypatch.setattr(servidor, "api", cliente)
    return falsa
