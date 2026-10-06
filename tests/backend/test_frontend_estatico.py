"""Spec: publicacao — FastAPI serve o build do React junto com a API em /api."""
import pytest
from fastapi.testclient import TestClient

from app.main import criar_app


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "index.html").write_text("<html>MarcaConsulta</html>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    return TestClient(criar_app(tmp_path))


def test_pagina_inicial_abre_sem_login(cliente):
    r = cliente.get("/")
    assert r.status_code == 200 and "MarcaConsulta" in r.text


def test_rota_do_react_devolve_index(cliente):
    assert "MarcaConsulta" in cliente.get("/minhas-consultas").text


def test_arquivo_estatico_e_servido(cliente):
    assert cliente.get("/assets/app.js").text == "console.log(1)"


def test_api_inexistente_devolve_404_json(cliente):
    r = cliente.get("/api/nao-existe")
    assert r.status_code == 404 and r.json()["detail"] == "Rota não encontrada."


def test_api_continua_funcionando(cliente):
    assert cliente.get("/api/health").json()["status"] == "ok"


def test_nao_sai_da_pasta_de_estaticos(cliente):
    assert "MarcaConsulta" in cliente.get("/..%2F..%2Fetc%2Fpasswd").text
