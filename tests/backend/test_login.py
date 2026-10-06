"""Spec: cadastro-e-login — login, renovação, logout e bloqueio."""
from datetime import datetime, timedelta, timezone

import jwt

from app.core.tempo import Relogio
from apoio import SENHA, criar_usuario

T0 = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)


def entrar(client, email, senha=SENHA):
    return client.post("/api/auth/login", json={"email": email, "senha": senha})


def test_login_devolve_access_de_30_min_e_refresh(client, db):
    Relogio.atual = T0
    u = criar_usuario(db, email="ana@teste.com")
    r = entrar(client, "ana@teste.com")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["refresh_token"]
    dados = jwt.decode(corpo["access_token"], options={"verify_signature": False})
    assert dados["sub"] == str(u.id) and dados["perfil"] == "paciente"
    assert dados["exp"] - dados["iat"] == 30 * 60


def test_access_token_expira_em_30_min(client, db):
    Relogio.atual = T0
    criar_usuario(db, email="ana@teste.com")
    token = entrar(client, "ana@teste.com").json()["access_token"]
    cab = {"Authorization": f"Bearer {token}"}
    Relogio.atual = T0 + timedelta(minutes=29)
    assert client.get("/api/auth/eu", headers=cab).status_code == 200
    Relogio.atual = T0 + timedelta(minutes=31)
    assert client.get("/api/auth/eu", headers=cab).status_code == 401


def test_refresh_vale_7_dias(client, db):
    Relogio.atual = T0
    criar_usuario(db, email="ana@teste.com")
    refresh = entrar(client, "ana@teste.com").json()["refresh_token"]
    Relogio.atual = T0 + timedelta(days=6, hours=23)
    assert client.post("/api/auth/renovar", json={"refresh_token": refresh}).status_code == 200
    Relogio.atual = T0 + timedelta(days=7, minutes=1)
    assert client.post("/api/auth/renovar", json={"refresh_token": refresh}).status_code == 401


def test_senha_errada_devolve_401_em_portugues(client, db):
    criar_usuario(db, email="ana@teste.com")
    r = entrar(client, "ana@teste.com", "errada123")
    assert r.status_code == 401
    assert r.json()["detail"] == "E-mail ou senha incorretos."


def test_cinco_erros_seguidos_bloqueiam_por_15_minutos(client, db):
    Relogio.atual = T0
    criar_usuario(db, email="ana@teste.com")
    for _ in range(4):
        assert entrar(client, "ana@teste.com", "errada123").status_code == 401
    assert entrar(client, "ana@teste.com", "errada123").status_code == 423
    # bloqueada mesmo com a senha certa
    Relogio.atual = T0 + timedelta(minutes=14)
    assert entrar(client, "ana@teste.com").status_code == 423
    Relogio.atual = T0 + timedelta(minutes=16)
    assert entrar(client, "ana@teste.com").status_code == 200


def test_acerto_zera_a_contagem_de_erros(client, db):
    criar_usuario(db, email="ana@teste.com")
    for _ in range(4):
        entrar(client, "ana@teste.com", "errada123")
    assert entrar(client, "ana@teste.com").status_code == 200
    for _ in range(4):
        assert entrar(client, "ana@teste.com", "errada123").status_code == 401


def test_logout_invalida_o_refresh_token(client, db):
    criar_usuario(db, email="ana@teste.com")
    tokens = entrar(client, "ana@teste.com").json()
    cab = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=cab).status_code == 204
    r = client.post("/api/auth/renovar", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401
