"""Spec: publicacao — comando seed com os dados de demonstração."""
from sqlalchemy import func, select

from app.agendamento.models import Consulta
from app.auth.models import Usuario
from app.clinicas.models import Especialidade, Profissional, Unidade
from app.core.tempo import Relogio, agora_utc
from app.seed import gerar_cpf, popular
from app.auth.service import cpf_valido
from apoio import local


def contar(db, modelo, *filtros):
    return db.scalar(select(func.count()).select_from(modelo).where(*filtros))


def test_seed_cria_os_dados_minimos_e_e_idempotente(db):
    Relogio.atual = local("2026-10-06 09:00")
    assert popular(db) is True
    assert contar(db, Unidade) == 3
    assert contar(db, Especialidade) == 12
    assert contar(db, Profissional) >= 40
    assert contar(db, Usuario, Usuario.perfil == "paciente") == 100
    agora = agora_utc()
    assert contar(db, Consulta, Consulta.inicio < agora) > 0
    assert contar(db, Consulta, Consulta.inicio > agora) > 0
    for perfil in ("paciente", "profissional", "recepcao", "admin"):
        assert db.scalar(select(Usuario).where(Usuario.email.like("%@demo.com"), Usuario.perfil == perfil))
    medico = db.scalar(select(Usuario).where(Usuario.email == "medico@demo.com"))
    assert db.scalar(select(Profissional).where(Profissional.usuario_id == medico.id))

    total = contar(db, Profissional)
    assert popular(db) is False
    assert contar(db, Profissional) == total


def test_cpfs_gerados_sao_validos():
    import random

    rng = random.Random(1)
    assert all(cpf_valido(gerar_cpf(rng)) for _ in range(50))
