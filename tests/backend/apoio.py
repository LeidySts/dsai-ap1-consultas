"""Fábricas e atalhos usados pelos testes do backend."""
from datetime import date
from functools import lru_cache

from app.auth.models import Usuario
from app.core.seguranca import criar_access_token, hash_senha

SENHA = "senha1234"


@lru_cache
def _hash_padrao() -> str:
    return hash_senha(SENHA)


def criar_usuario(db, perfil="paciente", email=None, nome="Fulano de Tal", cpf=None) -> Usuario:
    usuario = Usuario(
        nome=nome,
        email=email or f"{perfil}{db.query(Usuario).count() + 1}@teste.com",
        cpf=cpf,
        data_nascimento=date(1990, 1, 1) if perfil == "paciente" else None,
        telefone="91999990000",
        senha_hash=_hash_padrao(),
        perfil=perfil,
    )
    db.add(usuario)
    db.commit()
    return usuario


def auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {criar_access_token(usuario.id, usuario.perfil)}"}


def criar_unidade(db, nome="Unidade Centro", abertura="07:00", fechamento="19:00", dias=(0, 1, 2, 3, 4, 5)):
    from datetime import time

    from app.clinicas.models import Unidade
    from app.core.texto import normalizar

    unidade = Unidade(
        nome=nome, nome_busca=normalizar(nome), endereco="Rua A, 100", cep="66000000", telefone="9132220000",
        abertura=time.fromisoformat(abertura), fechamento=time.fromisoformat(fechamento),
        dias_funcionamento=list(dias),
    )
    db.add(unidade)
    db.commit()
    return unidade


def criar_especialidade(db, nome="Cardiologia", tipos=(("Consulta", 30, 25000),)):
    from app.clinicas.models import Especialidade, TipoConsulta
    from app.core.texto import normalizar

    especialidade = Especialidade(nome=nome, nome_busca=normalizar(nome))
    especialidade.tipos = [TipoConsulta(nome=n, duracao_min=d, preco_centavos=p) for n, d, p in tipos]
    db.add(especialidade)
    db.commit()
    return especialidade


def criar_profissional(db, nome="Dr. João Souza", especialidades=(), unidades=(), numero=None, usuario=None):
    from app.clinicas.models import Profissional
    from app.core.texto import normalizar

    total = db.query(Profissional).count()
    profissional = Profissional(
        nome=nome, nome_busca=normalizar(nome), conselho="CRM", registro_numero=numero or str(10000 + total),
        registro_uf="PA", biografia="Atende adultos.", especialidades=list(especialidades), unidades=list(unidades),
        usuario_id=usuario.id if usuario else None,
    )
    db.add(profissional)
    db.commit()
    return profissional


def local(texto: str):
    """'2026-10-12 08:00' no fuso de São Paulo -> datetime com fuso."""
    from datetime import datetime

    from app.core.tempo import FUSO_LOCAL

    return datetime.fromisoformat(texto).replace(tzinfo=FUSO_LOCAL)


def criar_faixa(db, profissional, unidade, dia_semana=0, inicio="08:00", fim="12:00"):
    from datetime import time

    from app.agenda.models import GradeHorario

    faixa = GradeHorario(
        profissional_id=profissional.id, unidade_id=unidade.id, dia_semana=dia_semana,
        hora_inicio=time.fromisoformat(inicio), hora_fim=time.fromisoformat(fim),
    )
    db.add(faixa)
    db.commit()
    return faixa


def criar_consulta(db, paciente, profissional, unidade, tipo, inicio, status="marcada", criado_por=None):
    from datetime import timedelta

    from app.agendamento.models import Consulta

    consulta = Consulta(
        paciente_id=paciente.id, profissional_id=profissional.id, unidade_id=unidade.id, tipo_consulta_id=tipo.id,
        inicio=inicio, fim=inicio + timedelta(minutes=tipo.duracao_min), status=status,
        preco_centavos=tipo.preco_centavos, criado_por_id=(criado_por or paciente).id,
    )
    db.add(consulta)
    db.commit()
    return consulta
