from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.agenda.service import Horario, carregar_dados_agenda, gerar_horarios, hoje_local
from app.clinicas.models import Especialidade, Profissional, TipoConsulta, Unidade
from app.core.erros import NaoEncontrado, RegraViolada
from app.core.tempo import FUSO_LOCAL, agora_utc
from app.core.texto import normalizar

POR_PAGINA = 10
JANELA_DIAS = 31
AVISO_SEM_HORARIO = "sem horários nos próximos 30 dias"
# turnos em hora local: [início, fim)
TURNOS = {"manha": (6, 12), "tarde": (12, 18), "noite": (18, 24)}
ORDENS = ("proximo", "preco")


@dataclass
class Filtro:
    especialidade_id: int | None = None
    unidade_id: int | None = None
    nome: str | None = None
    data: date | None = None
    turno: str | None = None
    ordem: str = "proximo"
    pagina: int = 1


def _tipo_de_referencia(profissional: Profissional, especialidade_id: int | None) -> TipoConsulta | None:
    """Tipo usado para o próximo horário (o mais curto) e o preço (o mais barato)."""
    especialidades = [e for e in profissional.especialidades if especialidade_id in (None, e.id)]
    tipos = [t for e in especialidades for t in e.tipos]
    return min(tipos, key=lambda t: (t.duracao_min, t.preco_centavos), default=None)


def _menor_preco(profissional: Profissional, especialidade_id: int | None) -> int | None:
    precos = [
        t.preco_centavos for e in profissional.especialidades if especialidade_id in (None, e.id) for t in e.tipos
    ]
    return min(precos, default=None)


def _no_turno(horario: Horario, turno: str | None) -> bool:
    if turno is None:
        return True
    inicio, fim = TURNOS[turno]
    return inicio <= horario.inicio.astimezone(FUSO_LOCAL).hour < fim


def buscar(db: Session, filtro: Filtro) -> dict:
    if filtro.turno is not None and filtro.turno not in TURNOS:
        raise RegraViolada("Turno inválido. Use manha, tarde ou noite.")
    if filtro.ordem not in ORDENS:
        raise RegraViolada("Ordenação inválida. Use proximo ou preco.")

    consulta = select(Profissional).where(Profissional.ativo.is_(True))
    if filtro.especialidade_id:
        consulta = consulta.where(Profissional.especialidades.any(Especialidade.id == filtro.especialidade_id))
    if filtro.unidade_id:
        consulta = consulta.where(Profissional.unidades.any(Unidade.id == filtro.unidade_id))
    if filtro.nome and normalizar(filtro.nome):
        texto = normalizar(filtro.nome)
        consulta = consulta.where(
            or_(
                Profissional.nome_busca.contains(texto),
                Profissional.especialidades.any(Especialidade.nome_busca.contains(texto)),
            )
        )
    profissionais = list(db.scalars(consulta))
    unidades = {u.id: u for u in db.scalars(select(Unidade))}

    hoje = hoje_local()
    inicio = max(filtro.data or hoje, hoje)
    fim = inicio + timedelta(days=JANELA_DIAS - 1)
    agendas = carregar_dados_agenda(db, [p.id for p in profissionais], inicio, fim)
    agora = agora_utc()

    resultados = []
    for prof in profissionais:
        tipo = _tipo_de_referencia(prof, filtro.especialidade_id)
        proximo = None
        if tipo is not None:
            proximo = next(
                (
                    h
                    for h in gerar_horarios(agendas[prof.id], tipo.duracao_min, inicio, fim, agora)
                    if filtro.unidade_id in (None, h.unidade_id) and _no_turno(h, filtro.turno)
                ),
                None,
            )
        resultados.append(
            {
                "id": prof.id,
                "nome": prof.nome,
                "foto_url": prof.foto_url,
                "especialidades": [e.nome for e in prof.especialidades],
                "unidades": [u.nome for u in prof.unidades if filtro.unidade_id in (None, u.id)],
                "nota_media": None,
                "preco_centavos": _menor_preco(prof, filtro.especialidade_id),
                "tipo_consulta_id": tipo.id if tipo else None,
                "proximo_horario": proximo
                and {"inicio": proximo.inicio, "unidade_id": proximo.unidade_id,
                     "unidade_nome": unidades[proximo.unidade_id].nome},
                "aviso": None if proximo else AVISO_SEM_HORARIO,
                "_nome_busca": prof.nome_busca,
            }
        )

    def chave(r: dict):
        sem_horario = r["proximo_horario"] is None
        if filtro.ordem == "preco":
            preco = r["preco_centavos"] if r["preco_centavos"] is not None else float("inf")
            return (sem_horario, preco, r["_nome_busca"])
        return (sem_horario, r["proximo_horario"]["inicio"] if r["proximo_horario"] else agora, r["_nome_busca"])

    resultados.sort(key=chave)
    pagina = max(filtro.pagina, 1)
    fatia = resultados[(pagina - 1) * POR_PAGINA : pagina * POR_PAGINA]
    return {
        "itens": fatia,
        "total": len(resultados),
        "pagina": pagina,
        "paginas": max(ceil(len(resultados) / POR_PAGINA), 1),
    }


def profissional_publico(db: Session, profissional_id: int) -> Profissional:
    profissional = db.get(Profissional, profissional_id)
    if profissional is None or not profissional.ativo:
        raise NaoEncontrado("Profissional não encontrado.")
    return profissional
