from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agenda import service
from app.agenda.models import Bloqueio, Feriado, GradeHorario
from app.agenda.schemas import BloqueioIn, BloqueioOut, FaixaIn, FaixaOut, FeriadoIn, FeriadoOut, HorarioLivre
from app.clinicas.models import Profissional
from app.clinicas.schemas import ProfissionalOut
from app.core.db import get_db
from app.core.erros import NaoEncontrado
from app.core.seguranca import exige_perfil

router = APIRouter(tags=["agenda"])
publico = APIRouter(prefix="/publico", tags=["publico"])
equipe = exige_perfil("admin", "recepcao", "profissional")
so_admin = exige_perfil("admin")
dono = exige_perfil("admin", "profissional")


def _profissional_editavel(db: Session, profissional_id: int, usuario) -> Profissional:
    profissional = service.obter_profissional(db, profissional_id)
    service.garantir_dono_ou_admin(usuario, profissional)
    return profissional


@router.get("/eu/profissional", response_model=ProfissionalOut)
def meu_cadastro_profissional(usuario=Depends(exige_perfil("profissional")), db: Session = Depends(get_db)):
    profissional = db.scalar(select(Profissional).where(Profissional.usuario_id == usuario.id))
    if profissional is None:
        raise NaoEncontrado("Seu usuário não está ligado a um cadastro de profissional.")
    return profissional


# ---------- grade ----------

@router.get("/profissionais/{profissional_id}/grade", response_model=list[FaixaOut], dependencies=[Depends(equipe)])
def listar_grade(profissional_id: int, db: Session = Depends(get_db)):
    return service.listar_grade(db, profissional_id)


@router.post("/profissionais/{profissional_id}/grade", response_model=FaixaOut, status_code=status.HTTP_201_CREATED)
def criar_faixa(profissional_id: int, dados: FaixaIn, usuario=Depends(dono), db: Session = Depends(get_db)):
    return service.criar_faixa(db, _profissional_editavel(db, profissional_id, usuario), dados)


@router.delete("/grade/{faixa_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_faixa(faixa_id: int, usuario=Depends(dono), db: Session = Depends(get_db)):
    faixa = db.get(GradeHorario, faixa_id)
    if faixa is None:
        raise NaoEncontrado("Faixa não encontrada.")
    _profissional_editavel(db, faixa.profissional_id, usuario)
    db.delete(faixa)
    db.commit()


# ---------- bloqueios ----------

@router.get(
    "/profissionais/{profissional_id}/bloqueios", response_model=list[BloqueioOut], dependencies=[Depends(equipe)]
)
def listar_bloqueios(profissional_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(Bloqueio).where(Bloqueio.profissional_id == profissional_id).order_by(Bloqueio.inicio)
    ).all()


@router.post(
    "/profissionais/{profissional_id}/bloqueios", response_model=BloqueioOut, status_code=status.HTTP_201_CREATED
)
def criar_bloqueio(profissional_id: int, dados: BloqueioIn, usuario=Depends(dono), db: Session = Depends(get_db)):
    return service.criar_bloqueio(db, _profissional_editavel(db, profissional_id, usuario), dados)


@router.delete("/bloqueios/{bloqueio_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_bloqueio(bloqueio_id: int, usuario=Depends(dono), db: Session = Depends(get_db)):
    bloqueio = db.get(Bloqueio, bloqueio_id)
    if bloqueio is None:
        raise NaoEncontrado("Bloqueio não encontrado.")
    _profissional_editavel(db, bloqueio.profissional_id, usuario)
    db.delete(bloqueio)
    db.commit()


# ---------- feriados ----------

@router.get("/feriados", response_model=list[FeriadoOut], dependencies=[Depends(equipe)])
def listar_feriados(db: Session = Depends(get_db)):
    return db.scalars(select(Feriado).order_by(Feriado.data)).all()


@router.post("/feriados", response_model=FeriadoOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(so_admin)])
def criar_feriado(dados: FeriadoIn, db: Session = Depends(get_db)):
    return service.criar_feriado(db, dados)


@router.delete("/feriados/{feriado_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(so_admin)])
def remover_feriado(feriado_id: int, db: Session = Depends(get_db)):
    feriado = db.get(Feriado, feriado_id)
    if feriado is None:
        raise NaoEncontrado("Feriado não encontrado.")
    db.delete(feriado)
    db.commit()


# ---------- horários livres (público) ----------

@publico.get("/profissionais/{profissional_id}/horarios-livres", response_model=list[HorarioLivre])
def horarios_livres(profissional_id: int, tipo_consulta_id: int, de: date, ate: date, db: Session = Depends(get_db)):
    profissional = service.obter_profissional(db, profissional_id)
    tipo = service.tipo_do_profissional(db, profissional, tipo_consulta_id)
    return service.horarios_livres(db, profissional, tipo, de, ate)

