from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.busca import service
from app.busca.schemas import Filtros, PaginaBusca, ProfissionalPublico
from app.clinicas.models import Especialidade, Unidade
from app.core.db import get_db

router = APIRouter(prefix="/publico", tags=["publico"])


@router.get("/filtros", response_model=Filtros)
def filtros(db: Session = Depends(get_db)):
    return {
        "especialidades": db.scalars(select(Especialidade).order_by(Especialidade.nome)).all(),
        "unidades": db.scalars(select(Unidade).where(Unidade.ativa.is_(True)).order_by(Unidade.nome)).all(),
    }


@router.get("/profissionais", response_model=PaginaBusca)
def buscar(
    especialidade_id: int | None = None,
    unidade_id: int | None = None,
    nome: str | None = None,
    data: date | None = None,
    turno: str | None = None,
    ordem: str = "proximo",
    pagina: int = 1,
    db: Session = Depends(get_db),
):
    filtro = service.Filtro(especialidade_id, unidade_id, nome, data, turno, ordem, pagina)
    return service.buscar(db, filtro)


@router.get("/profissionais/{profissional_id}", response_model=ProfissionalPublico)
def profissional(profissional_id: int, db: Session = Depends(get_db)):
    return service.profissional_publico(db, profissional_id)
