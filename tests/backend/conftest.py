"""Fixtures do backend. Os testes rodam em PostgreSQL de verdade:
TEST_DATABASE_URL, se definida; senão um PostgreSQL embutido (pgserver)."""
import os
import tempfile


def _url_banco_teste() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    import pgserver

    servidor = pgserver.get_server(os.path.join(tempfile.gettempdir(), "marcaconsulta-pg"), cleanup_mode=None)
    if "marcaconsulta_test" not in servidor.psql("select datname from pg_database;"):
        servidor.psql("create database marcaconsulta_test;")
    return servidor.get_uri("marcaconsulta_test")


os.environ["DATABASE_URL"] = _url_banco_teste()
os.environ.setdefault("JWT_SECRET", "segredo-de-teste")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import SessionLocal, engine  # noqa: E402
from app.core.tempo import Relogio  # noqa: E402
from app.main import app  # noqa: E402
from app.modelos import Base  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def _limpar_banco():
    yield
    Relogio.atual = None
    tabelas = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    if tabelas:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db():
    sessao = SessionLocal()
    yield sessao
    sessao.close()


@pytest.fixture
def client():
    return TestClient(app)
