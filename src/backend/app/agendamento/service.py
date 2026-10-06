from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agenda.service import carregar_dados_agenda, gerar_horarios, tipo_do_profissional
from app.agendamento.models import STATUS_ATIVOS, Consulta, HistoricoStatus
from app.agendamento.schemas import MarcarIn
from app.auth.models import Usuario
from app.auth.service import somente_digitos
from app.clinicas.models import Profissional
from app.core.erros import Conflito, NaoEncontrado, Proibido, RegraViolada
from app.core.tempo import FUSO_LOCAL, agora_utc

MAX_FUTURAS_MARCADAS = 3
MAX_REMARCACOES = 2
ANTECEDENCIA_CANCELAMENTO = timedelta(hours=24)
JANELA_FALTAS = timedelta(days=90)
FALTAS_PARA_BLOQUEIO = 3
DURACAO_BLOQUEIO_WEB = timedelta(days=30)
MSG_INDISPONIVEL = "Horário não está mais disponível."
EQUIPE = ("recepcao", "admin")

# transições permitidas: status atual -> próximos possíveis
TRANSICOES: dict[str, set[str]] = {
    "marcada": {"confirmada", "cancelada_paciente", "cancelada_clinica", "faltou"},
    "confirmada": {"em_atendimento", "cancelada_clinica"},
    "em_atendimento": {"realizada"},
    "realizada": set(),
    "cancelada_paciente": set(),
    "cancelada_clinica": set(),
    "faltou": set(),
}


def mudar_status(db: Session, consulta: Consulta, novo: str, autor: Usuario) -> None:
    if novo not in TRANSICOES.get(consulta.status, set()):
        raise RegraViolada(f"Não é possível mudar a consulta de '{consulta.status}' para '{novo}'.")
    db.add(HistoricoStatus(consulta_id=consulta.id, de_status=consulta.status, para_status=novo,
                           usuario_id=autor.id, em=agora_utc()))
    consulta.status = novo


def obter_consulta(db: Session, consulta_id: int, usuario: Usuario) -> Consulta:
    consulta = db.get(Consulta, consulta_id)
    if consulta is None:
        raise NaoEncontrado("Consulta não encontrada.")
    permitido = (
        usuario.perfil in EQUIPE
        or consulta.paciente_id == usuario.id
        or (usuario.perfil == "profissional" and consulta.profissional.usuario_id == usuario.id)
    )
    if not permitido:
        raise NaoEncontrado("Consulta não encontrada.")
    return consulta


# ---------- regras do paciente ----------

def bloqueado_na_web_ate(db: Session, paciente_id: int) -> datetime | None:
    """3 faltas dentro de 90 dias bloqueiam a marcação pela web por 30 dias após a 3ª."""
    agora = agora_utc()
    faltas = list(
        db.scalars(
            select(Consulta.inicio)
            .where(Consulta.paciente_id == paciente_id, Consulta.status == "faltou",
                   Consulta.inicio >= agora - JANELA_FALTAS - DURACAO_BLOQUEIO_WEB)
            .order_by(Consulta.inicio)
        )
    )
    ate = None
    for i in range(FALTAS_PARA_BLOQUEIO - 1, len(faltas)):
        if faltas[i] - faltas[i - FALTAS_PARA_BLOQUEIO + 1] <= JANELA_FALTAS:
            ate = faltas[i] + DURACAO_BLOQUEIO_WEB
    return ate if ate and ate > agora else None


def _validar_paciente(db: Session, paciente: Usuario, inicio: datetime, fim: datetime, pela_web: bool) -> None:
    if pela_web:
        ate = bloqueado_na_web_ate(db, paciente.id)
        if ate:
            raise RegraViolada(
                f"Por causa de 3 faltas, a marcação pela web está suspensa até {ate.astimezone(FUSO_LOCAL):%d/%m/%Y}. "
                "Procure a recepção."
            )
    sobreposta = db.scalar(
        select(Consulta.id).where(
            Consulta.paciente_id == paciente.id, Consulta.status.in_(STATUS_ATIVOS),
            Consulta.inicio < fim, Consulta.fim > inicio,
        )
    )
    if sobreposta:
        raise RegraViolada("Você já tem uma consulta neste horário.")
    futuras = db.scalar(
        select(func.count()).select_from(Consulta).where(
            Consulta.paciente_id == paciente.id, Consulta.status == "marcada", Consulta.inicio > agora_utc()
        )
    )
    if futuras >= MAX_FUTURAS_MARCADAS:
        raise RegraViolada("Limite de 3 consultas futuras marcadas atingido.")


def _horario_livre(db: Session, profissional: Profissional, duracao_min: int, inicio: datetime, unidade_id: int) -> bool:
    dia = inicio.astimezone(FUSO_LOCAL).date()
    dados = carregar_dados_agenda(db, [profissional.id], dia, dia)[profissional.id]
    alvo = inicio.astimezone(timezone.utc)
    return any(
        h.inicio == alvo and h.unidade_id == unidade_id
        for h in gerar_horarios(dados, duracao_min, dia, dia, agora_utc())
    )


def _criar(db: Session, autor: Usuario, paciente: Usuario, dados: MarcarIn, remarcacoes: int = 0,
           origem_id: int | None = None) -> Consulta:
    """Valida e insere sem commit. O lock no profissional serializa pedidos simultâneos."""
    if dados.forma_pagamento != "particular":
        raise RegraViolada("No momento só aceitamos pagamento particular.")
    profissional = db.scalar(
        select(Profissional).where(Profissional.id == dados.profissional_id).with_for_update()
    )
    if profissional is None or not profissional.ativo:
        raise NaoEncontrado("Profissional não encontrado.")
    tipo = tipo_do_profissional(db, profissional, dados.tipo_consulta_id)
    inicio = dados.inicio
    if inicio.tzinfo is None:
        raise RegraViolada("Informe o horário com fuso (ISO 8601).")
    fim = inicio + timedelta(minutes=tipo.duracao_min)
    if not _horario_livre(db, profissional, tipo.duracao_min, inicio, dados.unidade_id):
        raise Conflito(MSG_INDISPONIVEL)
    _validar_paciente(db, paciente, inicio, fim, pela_web=autor.perfil == "paciente")
    consulta = Consulta(
        paciente_id=paciente.id, profissional_id=profissional.id, unidade_id=dados.unidade_id,
        tipo_consulta_id=tipo.id, inicio=inicio, fim=fim, status="marcada",
        forma_pagamento=dados.forma_pagamento, preco_centavos=tipo.preco_centavos,
        remarcacoes=remarcacoes, consulta_origem_id=origem_id, criado_por_id=autor.id,
    )
    db.add(consulta)
    db.flush()
    db.add(HistoricoStatus(consulta_id=consulta.id, de_status=None, para_status="marcada",
                           usuario_id=autor.id, em=agora_utc()))
    return consulta


def _paciente_alvo(db: Session, autor: Usuario, paciente_id: int | None) -> Usuario:
    if autor.perfil == "paciente":
        return autor
    if autor.perfil not in EQUIPE:
        raise Proibido("Seu perfil não pode marcar consultas.")
    if paciente_id is None:
        raise RegraViolada("Informe o paciente.")
    paciente = db.get(Usuario, paciente_id)
    if paciente is None or paciente.perfil != "paciente" or not paciente.ativo:
        raise NaoEncontrado("Paciente não encontrado.")
    return paciente


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:  # rede de segurança: índice único parcial
        db.rollback()
        raise Conflito(MSG_INDISPONIVEL) from exc


def marcar(db: Session, autor: Usuario, dados: MarcarIn) -> Consulta:
    paciente = _paciente_alvo(db, autor, dados.paciente_id)
    try:
        consulta = _criar(db, autor, paciente, dados)
    except Exception:
        db.rollback()
        raise
    _commit(db)
    return consulta


# ---------- cancelar e remarcar ----------

def pode_cancelar(consulta: Consulta, usuario: Usuario) -> bool:
    if consulta.status not in ("marcada", "confirmada"):
        return False
    if usuario.perfil in EQUIPE:
        return True
    return (
        usuario.id == consulta.paciente_id
        and consulta.status == "marcada"
        and consulta.inicio - agora_utc() >= ANTECEDENCIA_CANCELAMENTO
    )


def pode_remarcar(consulta: Consulta, usuario: Usuario) -> bool:
    return pode_cancelar(consulta, usuario) and consulta.remarcacoes < MAX_REMARCACOES


def _cancelar_sem_commit(db: Session, consulta: Consulta, autor: Usuario) -> None:
    if consulta.status not in ("marcada", "confirmada"):
        raise RegraViolada(f"Não é possível cancelar uma consulta com status '{consulta.status}'.")
    if autor.perfil in EQUIPE:
        mudar_status(db, consulta, "cancelada_clinica", autor)
        return
    if autor.id != consulta.paciente_id:
        raise NaoEncontrado("Consulta não encontrada.")
    if consulta.inicio - agora_utc() < ANTECEDENCIA_CANCELAMENTO:
        raise RegraViolada("Faltam menos de 24 horas: só a recepção pode cancelar ou remarcar.")
    mudar_status(db, consulta, "cancelada_paciente", autor)


def cancelar(db: Session, consulta: Consulta, autor: Usuario) -> Consulta:
    _cancelar_sem_commit(db, consulta, autor)
    db.commit()
    return consulta


def remarcar(db: Session, consulta: Consulta, autor: Usuario, inicio: datetime, unidade_id: int | None) -> Consulta:
    """Cancela a original e marca a nova numa transação: se a nova falhar, nada muda."""
    if consulta.remarcacoes >= MAX_REMARCACOES:
        raise RegraViolada("Esta consulta já foi remarcada 2 vezes.")
    paciente = db.get(Usuario, consulta.paciente_id)
    dados = MarcarIn(profissional_id=consulta.profissional_id, unidade_id=unidade_id or consulta.unidade_id,
                     tipo_consulta_id=consulta.tipo_consulta_id, inicio=inicio,
                     forma_pagamento=consulta.forma_pagamento, paciente_id=paciente.id)
    try:
        _cancelar_sem_commit(db, consulta, autor)
        db.flush()
        nova = _criar(db, autor, paciente, dados, remarcacoes=consulta.remarcacoes + 1, origem_id=consulta.id)
    except Exception:
        db.rollback()
        raise
    _commit(db)
    return nova


# ---------- consultas ----------

def com_permissoes(consulta: Consulta, usuario: Usuario) -> dict:
    dados = {c: getattr(consulta, c) for c in (
        "id", "inicio", "fim", "status", "forma_pagamento", "preco_centavos", "remarcacoes",
        "paciente", "profissional", "unidade", "tipo_consulta",
    )}
    return {**dados, "pode_cancelar": pode_cancelar(consulta, usuario),
            "pode_remarcar": pode_remarcar(consulta, usuario)}


def minhas(db: Session, paciente: Usuario) -> dict:
    agora = agora_utc()
    consultas = list(db.scalars(select(Consulta).where(Consulta.paciente_id == paciente.id)))
    proximas = sorted((c for c in consultas if c.fim > agora), key=lambda c: c.inicio)
    passadas = sorted((c for c in consultas if c.fim <= agora), key=lambda c: c.inicio, reverse=True)
    return {
        "proximas": [com_permissoes(c, paciente) for c in proximas],
        "passadas": [com_permissoes(c, paciente) for c in passadas],
    }


def historico(db: Session, consulta: Consulta) -> list[HistoricoStatus]:
    return list(db.scalars(
        select(HistoricoStatus).where(HistoricoStatus.consulta_id == consulta.id).order_by(HistoricoStatus.id)
    ))


def agenda_profissional(db: Session, profissional_id: int, de: datetime, ate: datetime) -> list[Consulta]:
    return list(db.scalars(
        select(Consulta)
        .where(Consulta.profissional_id == profissional_id, Consulta.inicio >= de, Consulta.inicio < ate)
        .order_by(Consulta.inicio)
    ))


def buscar_pacientes(db: Session, q: str) -> list[Usuario]:
    texto = q.strip()
    if len(texto) < 2:
        return []
    filtros = [func.lower(Usuario.nome).contains(texto.lower()), Usuario.email.contains(texto.lower())]
    if somente_digitos(texto):
        filtros.append(Usuario.cpf.contains(somente_digitos(texto)))
    return list(db.scalars(
        select(Usuario).where(Usuario.perfil == "paciente", Usuario.ativo.is_(True), or_(*filtros))
        .order_by(Usuario.nome).limit(20)
    ))

