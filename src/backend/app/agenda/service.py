from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agenda.models import Bloqueio, Feriado, GradeHorario
from app.agenda.schemas import BloqueioIn, FaixaIn, FeriadoIn
from app.agendamento.models import STATUS_ATIVOS, Consulta
from app.auth.models import Usuario
from app.clinicas.models import Profissional, TipoConsulta, Unidade
from app.core.erros import Conflito, NaoEncontrado, Proibido, RegraViolada
from app.core.tempo import FUSO_LOCAL, agora_utc

ANTECEDENCIA_MINIMA = timedelta(hours=2)
MAX_DIAS_INTERVALO = 31


# ---------- permissões ----------

def obter_profissional(db: Session, profissional_id: int) -> Profissional:
    profissional = db.get(Profissional, profissional_id)
    if profissional is None:
        raise NaoEncontrado("Profissional não encontrado.")
    return profissional


def garantir_dono_ou_admin(usuario: Usuario, profissional: Profissional) -> None:
    if usuario.perfil == "admin":
        return
    if usuario.perfil == "profissional" and profissional.usuario_id == usuario.id:
        return
    raise Proibido("Você só pode alterar a sua própria agenda.")


# ---------- grade semanal ----------

def _sobrepoe(a_inicio, a_fim, b_inicio, b_fim) -> bool:
    return a_inicio < b_fim and b_inicio < a_fim


def criar_faixa(db: Session, profissional: Profissional, dados: FaixaIn) -> GradeHorario:
    if dados.hora_inicio >= dados.hora_fim:
        raise RegraViolada("A hora de início deve ser antes da hora de fim.")
    unidade = db.get(Unidade, dados.unidade_id)
    if unidade is None or unidade not in profissional.unidades:
        raise RegraViolada("O profissional não atende nesta unidade.")
    if dados.dia_semana not in unidade.dias_funcionamento:
        raise RegraViolada("A unidade não funciona neste dia da semana.")
    if dados.hora_inicio < unidade.abertura or dados.hora_fim > unidade.fechamento:
        raise RegraViolada(
            f"A faixa deve ficar dentro do horário da unidade ({unidade.abertura:%H:%M}–{unidade.fechamento:%H:%M})."
        )
    existentes = db.scalars(
        select(GradeHorario).where(
            GradeHorario.profissional_id == profissional.id, GradeHorario.dia_semana == dados.dia_semana
        )
    )
    for faixa in existentes:
        if _sobrepoe(dados.hora_inicio, dados.hora_fim, faixa.hora_inicio, faixa.hora_fim):
            raise RegraViolada(
                f"A faixa se sobrepõe a outra já cadastrada ({faixa.hora_inicio:%H:%M}–{faixa.hora_fim:%H:%M})."
            )
    faixa = GradeHorario(profissional_id=profissional.id, **dados.model_dump())
    db.add(faixa)
    db.commit()
    return faixa


def listar_grade(db: Session, profissional_id: int) -> list[GradeHorario]:
    return list(
        db.scalars(
            select(GradeHorario)
            .where(GradeHorario.profissional_id == profissional_id)
            .order_by(GradeHorario.dia_semana, GradeHorario.hora_inicio)
        )
    )


# ---------- bloqueios ----------

def consultas_ativas_entre(db: Session, profissional_id: int, inicio: datetime, fim: datetime) -> list[Consulta]:
    return list(
        db.scalars(
            select(Consulta)
            .where(
                Consulta.profissional_id == profissional_id,
                Consulta.status.in_(STATUS_ATIVOS),
                Consulta.inicio < fim,
                Consulta.fim > inicio,
            )
            .order_by(Consulta.inicio)
        )
    )


def criar_bloqueio(db: Session, profissional: Profissional, dados: BloqueioIn) -> Bloqueio:
    if dados.inicio >= dados.fim:
        raise RegraViolada("O início do bloqueio deve ser antes do fim.")
    colisoes = consultas_ativas_entre(db, profissional.id, dados.inicio, dados.fim)
    if colisoes:
        raise Conflito(
            "O bloqueio colide com consultas marcadas. Remarque ou cancele antes.",
            consultas=[{"id": c.id, "inicio": c.inicio.isoformat(), "paciente": c.paciente.nome} for c in colisoes],
        )
    bloqueio = Bloqueio(profissional_id=profissional.id, **dados.model_dump())
    db.add(bloqueio)
    db.commit()
    return bloqueio


# ---------- feriados ----------

def criar_feriado(db: Session, dados: FeriadoIn) -> Feriado:
    if dados.unidade_id is not None and db.get(Unidade, dados.unidade_id) is None:
        raise RegraViolada("Unidade inexistente.")
    existe = db.scalar(
        select(Feriado.id).where(
            Feriado.data == dados.data,
            Feriado.unidade_id.is_(None) if dados.unidade_id is None else Feriado.unidade_id == dados.unidade_id,
        )
    )
    if existe:
        raise Conflito("Já existe um feriado nesta data.")
    feriado = Feriado(**dados.model_dump())
    db.add(feriado)
    db.commit()
    return feriado


# ---------- horários livres ----------

@dataclass(frozen=True)
class Horario:
    inicio: datetime
    fim: datetime
    unidade_id: int


@dataclass
class DadosAgenda:
    """Tudo que o cálculo precisa de um profissional, carregado em lote."""

    grade: list[GradeHorario]
    ocupados: list[tuple[datetime, datetime]]  # bloqueios + consultas ativas
    feriados: dict[date, set[int | None]]  # data -> unidades (None = nacional)


def gerar_horarios(dados: DadosAgenda, duracao_min: int, de: date, ate: date, agora: datetime) -> Iterator[Horario]:
    """Gera, em ordem, os inícios livres entre `de` e `ate` (datas locais, inclusive)."""
    passo = timedelta(minutes=duracao_min)
    minimo = agora + ANTECEDENCIA_MINIMA
    por_dia = defaultdict(list)
    for faixa in dados.grade:
        por_dia[faixa.dia_semana].append(faixa)
    ocupados = sorted(dados.ocupados)
    dia = de
    while dia <= ate:
        unidades_em_feriado = dados.feriados.get(dia, set())
        horarios_do_dia = []
        if None not in unidades_em_feriado:
            for faixa in por_dia.get(dia.weekday(), []):
                if faixa.unidade_id in unidades_em_feriado:
                    continue
                inicio = datetime.combine(dia, faixa.hora_inicio, FUSO_LOCAL).astimezone(timezone.utc)
                limite = datetime.combine(dia, faixa.hora_fim, FUSO_LOCAL).astimezone(timezone.utc)
                while inicio + passo <= limite:
                    fim = inicio + passo
                    if inicio >= minimo and not any(_sobrepoe(inicio, fim, o_i, o_f) for o_i, o_f in ocupados):
                        horarios_do_dia.append(Horario(inicio, fim, faixa.unidade_id))
                    inicio = fim
        yield from sorted(horarios_do_dia, key=lambda h: h.inicio)
        dia += timedelta(days=1)


def _intervalo_utc(de: date, ate: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(de, time.min, FUSO_LOCAL).astimezone(timezone.utc),
        datetime.combine(ate + timedelta(days=1), time.min, FUSO_LOCAL).astimezone(timezone.utc),
    )


def carregar_dados_agenda(
    db: Session, profissional_ids: Iterable[int], de: date, ate: date
) -> dict[int, DadosAgenda]:
    """Carrega grade, bloqueios, consultas e feriados de vários profissionais com 4 consultas ao banco."""
    ids = list(profissional_ids)
    inicio, fim = _intervalo_utc(de, ate)
    dados = {pid: DadosAgenda(grade=[], ocupados=[], feriados={}) for pid in ids}
    if not ids:
        return dados
    for faixa in db.scalars(
        select(GradeHorario)
        .join(Unidade, Unidade.id == GradeHorario.unidade_id)
        .where(GradeHorario.profissional_id.in_(ids), Unidade.ativa.is_(True))
    ):
        dados[faixa.profissional_id].grade.append(faixa)
    for pid, b_inicio, b_fim in db.execute(
        select(Bloqueio.profissional_id, Bloqueio.inicio, Bloqueio.fim).where(
            Bloqueio.profissional_id.in_(ids), Bloqueio.inicio < fim, Bloqueio.fim > inicio
        )
    ):
        dados[pid].ocupados.append((b_inicio, b_fim))
    for pid, c_inicio, c_fim in db.execute(
        select(Consulta.profissional_id, Consulta.inicio, Consulta.fim).where(
            Consulta.profissional_id.in_(ids),
            Consulta.status.in_(STATUS_ATIVOS),
            Consulta.inicio < fim,
            Consulta.fim > inicio,
        )
    ):
        dados[pid].ocupados.append((c_inicio, c_fim))
    feriados: dict[date, set[int | None]] = defaultdict(set)
    for data, unidade_id in db.execute(select(Feriado.data, Feriado.unidade_id).where(Feriado.data.between(de, ate))):
        feriados[data].add(unidade_id)
    for item in dados.values():
        item.feriados = feriados
    return dados


def validar_intervalo(de: date, ate: date) -> None:
    if ate < de:
        raise RegraViolada("A data final deve ser igual ou posterior à inicial.")
    if (ate - de).days + 1 > MAX_DIAS_INTERVALO:
        raise RegraViolada("O intervalo máximo é de 31 dias.")


def tipo_do_profissional(db: Session, profissional: Profissional, tipo_consulta_id: int) -> TipoConsulta:
    tipo = db.get(TipoConsulta, tipo_consulta_id)
    if tipo is None or tipo.especialidade_id not in {e.id for e in profissional.especialidades}:
        raise RegraViolada("Este tipo de consulta não é atendido por este profissional.")
    return tipo


def horarios_livres(
    db: Session, profissional: Profissional, tipo: TipoConsulta, de: date, ate: date
) -> list[Horario]:
    validar_intervalo(de, ate)
    if not profissional.ativo:
        return []
    dados = carregar_dados_agenda(db, [profissional.id], de, ate)[profissional.id]
    return list(gerar_horarios(dados, tipo.duracao_min, de, ate, agora_utc()))


def hoje_local() -> date:
    return agora_utc().astimezone(FUSO_LOCAL).date()
