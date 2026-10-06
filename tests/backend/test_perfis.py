"""Spec: cadastro-e-login (perfis e 403) e visão geral (rotas exigem autenticação)."""
import re

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.erros import ErroDominio, tratar_erro_dominio
from app.core.seguranca import exige_perfil
from app.main import app
from apoio import auth, criar_usuario


@pytest.fixture
def cliente_restrito():
    teste = FastAPI()
    teste.add_exception_handler(ErroDominio, tratar_erro_dominio)

    @teste.get("/so-admin")
    def so_admin(_=Depends(exige_perfil("admin"))):
        return {"ok": True}

    return TestClient(teste)


@pytest.mark.parametrize("perfil", ["paciente", "profissional", "recepcao"])
def test_perfil_sem_permissao_recebe_403(cliente_restrito, db, perfil):
    r = cliente_restrito.get("/so-admin", headers=auth(criar_usuario(db, perfil)))
    assert r.status_code == 403
    assert r.json()["detail"] == "Seu perfil não tem permissão para esta ação."


def test_perfil_permitido_passa(cliente_restrito, db):
    assert cliente_restrito.get("/so-admin", headers=auth(criar_usuario(db, "admin"))).status_code == 200


def test_sem_token_recebe_401(client):
    assert client.get("/api/auth/eu").status_code == 401


def test_token_invalido_recebe_401(client):
    assert client.get("/api/auth/eu", headers={"Authorization": "Bearer lixo"}).status_code == 401


def test_rotas_protegidas_exigem_token(client):
    publicas = {"/api/health", "/api/auth/cadastro", "/api/auth/login", "/api/auth/renovar"}
    for rota in app.routes:
        caminho = getattr(rota, "path", "")
        if not caminho.startswith("/api") or caminho in publicas or caminho.startswith("/api/publico"):
            continue
        caminho = re.sub(r"\{[^}]+\}", "1", caminho)
        metodo = sorted(rota.methods)[0]
        r = client.request(metodo, caminho)
        assert r.status_code == 401, f"{metodo} {caminho} devolveu {r.status_code}"


def test_rotas_publicas_nao_exigem_token(client):
    assert client.get("/api/health").status_code == 200
    assert client.post("/api/auth/login", json={"email": "x@teste.com", "senha": "x"}).status_code == 401
