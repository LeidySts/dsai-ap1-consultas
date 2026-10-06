import re

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.clinicas.models import Especialidade, Profissional, TipoConsulta, Unidade
from app.clinicas.schemas import (
    EspecialidadeIn,
    ProfissionalEdicao,
    ProfissionalIn,
    TipoConsultaEdicao,
    TipoConsultaIn,
    UnidadeEdicao,
    UnidadeIn,
)
from app.core.erros import Conflito, NaoEncontrado, RegraViolada
from app.core.texto import normalizar

POR_PAGINA_ADMIN = 20
ORDENS = {"nome": "nome_busca", "-nome": "nome_busca", "recentes": "criado_em"}


def obter(db: Session, modelo, id_: int, rotulo: str):
    objeto = db.get(modelo, id_)
    if objeto is None:
        raise NaoEncontrado(f"{rotulo} não encontrado(a).")
    return objeto


def filtrar_e_ordenar(consulta: Select, modelo, q: str | None, ordem: str) -> Select:
    if q:
        consulta = consulta.where(modelo.nome_busca.contains(normalizar(q)))
    if ordem not in ORDENS:
        raise RegraViolada("Ordenação inválida. Use nome, -nome ou recentes.")
    coluna = getattr(modelo, ORDENS[ordem])
    return consulta.order_by(coluna.desc() if ordem in ("-nome", "recentes") else coluna, modelo.id)


# ---------- unidades ----------

def _validar_unidade(dados: dict) -> dict:
    if "cep" in dados and dados["cep"] is not None:
        cep = re.sub(r"\D", "", dados["cep"])
        if len(cep) != 8:
            raise RegraViolada("CEP deve ter 8 dígitos.")
        dados["cep"] = cep
    dias = dados.get("dias_funcionamento")
    if dias is not None:
        if any(d not in range(7) for d in dias):
            raise RegraViolada("Dias de funcionamento devem estar entre 0 (segunda) e 6 (domingo).")
        dados["dias_funcionamento"] = sorted(set(dias))
    return dados


def criar_unidade(db: Session, dados: UnidadeIn) -> Unidade:
    valores = _validar_unidade(dados.model_dump())
    if valores["abertura"] >= valores["fechamento"]:
        raise RegraViolada("O horário de abertura deve ser antes do fechamento.")
    unidade = Unidade(**valores, nome_busca=normalizar(valores["nome"]))
    db.add(unidade)
    db.commit()
    return unidade


def editar_unidade(db: Session, unidade_id: int, dados: UnidadeEdicao) -> Unidade:
    unidade = obter(db, Unidade, unidade_id, "Unidade")
    for campo, valor in _validar_unidade(dados.model_dump(exclude_unset=True)).items():
        setattr(unidade, campo, valor)
    if unidade.abertura >= unidade.fechamento:
        raise RegraViolada("O horário de abertura deve ser antes do fechamento.")
    unidade.nome_busca = normalizar(unidade.nome)
    db.commit()
    return unidade


# ---------- especialidades e tipos ----------

def _nome_especialidade_livre(db: Session, nome: str, exceto_id: int | None = None) -> None:
    consulta = select(Especialidade.id).where(Especialidade.nome_busca == normalizar(nome))
    if exceto_id:
        consulta = consulta.where(Especialidade.id != exceto_id)
    if db.scalar(consulta):
        raise Conflito("Já existe uma especialidade com este nome.")


def criar_especialidade(db: Session, dados: EspecialidadeIn) -> Especialidade:
    nome = dados.nome.strip()
    _nome_especialidade_livre(db, nome)
    especialidade = Especialidade(nome=nome, nome_busca=normalizar(nome))
    db.add(especialidade)
    db.commit()
    return especialidade


def editar_especialidade(db: Session, especialidade_id: int, dados: EspecialidadeIn) -> Especialidade:
    especialidade = obter(db, Especialidade, especialidade_id, "Especialidade")
    nome = dados.nome.strip()
    _nome_especialidade_livre(db, nome, exceto_id=especialidade_id)
    especialidade.nome, especialidade.nome_busca = nome, normalizar(nome)
    db.commit()
    return especialidade


def validar_duracao(duracao_min: int) -> None:
    if not 15 <= duracao_min <= 120 or duracao_min % 5:
        raise RegraViolada("A duração deve ser de 15 a 120 minutos, em múltiplos de 5.")


def criar_tipo_consulta(db: Session, especialidade_id: int, dados: TipoConsultaIn) -> TipoConsulta:
    obter(db, Especialidade, especialidade_id, "Especialidade")
    validar_duracao(dados.duracao_min)
    tipo = TipoConsulta(especialidade_id=especialidade_id, **dados.model_dump())
    db.add(tipo)
    db.commit()
    return tipo


def editar_tipo_consulta(db: Session, tipo_id: int, dados: TipoConsultaEdicao) -> TipoConsulta:
    tipo = obter(db, TipoConsulta, tipo_id, "Tipo de consulta")
    valores = dados.model_dump(exclude_unset=True)
    if "duracao_min" in valores:
        validar_duracao(valores["duracao_min"])
    for campo, valor in valores.items():
        setattr(tipo, campo, valor)
    db.commit()
    return tipo


# ---------- profissionais ----------

def _registro_livre(db: Session, conselho: str, numero: str, uf: str, exceto_id: int | None = None) -> None:
    consulta = select(Profissional.id).where(
        Profissional.conselho == conselho, Profissional.registro_numero == numero, Profissional.registro_uf == uf
    )
    if exceto_id:
        consulta = consulta.where(Profissional.id != exceto_id)
    if db.scalar(consulta):
        raise Conflito(f"Já existe um profissional com o registro {conselho} {numero}/{uf}.")


def _carregar(db: Session, modelo, ids: list[int], rotulo: str) -> list:
    objetos = db.scalars(select(modelo).where(modelo.id.in_(ids))).all()
    if len(objetos) != len(set(ids)):
        raise RegraViolada(f"{rotulo} inexistente na lista.")
    return list(objetos)


def criar_profissional(db: Session, dados: ProfissionalIn, usuario_id: int | None = None) -> Profissional:
    conselho, uf = dados.conselho.strip().upper(), dados.registro_uf.upper()
    numero = dados.registro_numero.strip()
    _registro_livre(db, conselho, numero, uf)
    profissional = Profissional(
        usuario_id=usuario_id,
        nome=dados.nome.strip(),
        nome_busca=normalizar(dados.nome),
        conselho=conselho,
        registro_numero=numero,
        registro_uf=uf,
        foto_url=dados.foto_url,
        biografia=dados.biografia,
        especialidades=_carregar(db, Especialidade, dados.especialidade_ids, "Especialidade"),
        unidades=_carregar(db, Unidade, dados.unidade_ids, "Unidade"),
    )
    db.add(profissional)
    db.commit()
    return profissional


def editar_profissional(db: Session, profissional_id: int, dados: ProfissionalEdicao) -> Profissional:
    profissional = obter(db, Profissional, profissional_id, "Profissional")
    valores = dados.model_dump(exclude_unset=True)
    if "especialidade_ids" in valores:
        profissional.especialidades = _carregar(db, Especialidade, valores.pop("especialidade_ids"), "Especialidade")
    if "unidade_ids" in valores:
        profissional.unidades = _carregar(db, Unidade, valores.pop("unidade_ids"), "Unidade")
    for campo, valor in valores.items():
        setattr(profissional, campo, valor.strip().upper() if campo in ("conselho", "registro_uf") else valor)
    _registro_livre(db, profissional.conselho, profissional.registro_numero, profissional.registro_uf, profissional.id)
    profissional.nome_busca = normalizar(profissional.nome)
    db.commit()
    return profissional


# ---------- desativação ----------

def _pendentes(db: Session, coluna: str, valor: int) -> list:
    from app.agendamento.models import STATUS_ATIVOS, Consulta
    from app.core.tempo import agora_utc

    return list(db.scalars(
        select(Consulta)
        .where(getattr(Consulta, coluna) == valor, Consulta.status.in_(STATUS_ATIVOS), Consulta.inicio > agora_utc())
        .order_by(Consulta.inicio)
    ))


def _conflito_pendentes(consultas: list, alvo: str) -> Conflito:
    return Conflito(
        f"{alvo} tem consultas futuras. Remarque ou cancele antes de desativar.",
        consultas=[{"id": c.id, "inicio": c.inicio.isoformat(), "paciente": c.paciente.nome,
                    "profissional": c.profissional.nome} for c in consultas],
    )


def desativar_unidade(db: Session, unidade_id: int) -> Unidade:
    unidade = obter(db, Unidade, unidade_id, "Unidade")
    pendentes = _pendentes(db, "unidade_id", unidade_id)
    if pendentes:
        raise _conflito_pendentes(pendentes, "A unidade")
    unidade.ativa = False
    db.commit()
    return unidade


def desativar_profissional(db: Session, profissional_id: int) -> Profissional:
    profissional = obter(db, Profissional, profissional_id, "Profissional")
    pendentes = _pendentes(db, "profissional_id", profissional_id)
    if pendentes:
        raise _conflito_pendentes(pendentes, "O profissional")
    profissional.ativo = False
    db.commit()
    return profissional
