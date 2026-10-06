from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinicas import service
from app.clinicas.models import Especialidade, Profissional, Unidade
from app.clinicas.schemas import (
    EspecialidadeIn,
    EspecialidadeOut,
    ProfissionalEdicao,
    ProfissionalIn,
    ProfissionalOut,
    TipoConsultaEdicao,
    TipoConsultaIn,
    TipoConsultaOut,
    UnidadeEdicao,
    UnidadeIn,
    UnidadeOut,
)
from app.core.db import get_db
from app.core.paginacao import Pagina, paginar
from app.core.seguranca import exige_perfil

router = APIRouter(tags=["clinicas"])
so_admin = exige_perfil("admin")
equipe = exige_perfil("admin", "recepcao", "profissional")


def _listar(db: Session, modelo, pagina: int, q: str | None, ordem: str):
    consulta = service.filtrar_e_ordenar(select(modelo), modelo, q, ordem)
    return paginar(db, consulta, pagina, service.POR_PAGINA_ADMIN)


# ---------- unidades ----------

@router.get("/unidades", response_model=Pagina[UnidadeOut], dependencies=[Depends(equipe)])
def listar_unidades(pagina: int = 1, q: str | None = None, ordem: str = "nome", db: Session = Depends(get_db)):
    return _listar(db, Unidade, pagina, q, ordem)


@router.post("/unidades", response_model=UnidadeOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(so_admin)])
def criar_unidade(dados: UnidadeIn, db: Session = Depends(get_db)):
    return service.criar_unidade(db, dados)


@router.patch("/unidades/{unidade_id}", response_model=UnidadeOut, dependencies=[Depends(so_admin)])
def editar_unidade(unidade_id: int, dados: UnidadeEdicao, db: Session = Depends(get_db)):
    return service.editar_unidade(db, unidade_id, dados)


# ---------- especialidades ----------

@router.get("/especialidades", response_model=Pagina[EspecialidadeOut], dependencies=[Depends(equipe)])
def listar_especialidades(pagina: int = 1, q: str | None = None, ordem: str = "nome", db: Session = Depends(get_db)):
    return _listar(db, Especialidade, pagina, q, ordem)


@router.post(
    "/especialidades", response_model=EspecialidadeOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(so_admin)]
)
def criar_especialidade(dados: EspecialidadeIn, db: Session = Depends(get_db)):
    return service.criar_especialidade(db, dados)


@router.patch("/especialidades/{especialidade_id}", response_model=EspecialidadeOut, dependencies=[Depends(so_admin)])
def editar_especialidade(especialidade_id: int, dados: EspecialidadeIn, db: Session = Depends(get_db)):
    return service.editar_especialidade(db, especialidade_id, dados)


@router.post(
    "/especialidades/{especialidade_id}/tipos-consulta",
    response_model=TipoConsultaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(so_admin)],
)
def criar_tipo(especialidade_id: int, dados: TipoConsultaIn, db: Session = Depends(get_db)):
    return service.criar_tipo_consulta(db, especialidade_id, dados)


@router.patch("/tipos-consulta/{tipo_id}", response_model=TipoConsultaOut, dependencies=[Depends(so_admin)])
def editar_tipo(tipo_id: int, dados: TipoConsultaEdicao, db: Session = Depends(get_db)):
    return service.editar_tipo_consulta(db, tipo_id, dados)


# ---------- profissionais ----------

@router.get("/profissionais", response_model=Pagina[ProfissionalOut], dependencies=[Depends(equipe)])
def listar_profissionais(pagina: int = 1, q: str | None = None, ordem: str = "nome", db: Session = Depends(get_db)):
    return _listar(db, Profissional, pagina, q, ordem)


@router.post(
    "/profissionais", response_model=ProfissionalOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(so_admin)]
)
def criar_profissional(dados: ProfissionalIn, db: Session = Depends(get_db)):
    return service.criar_profissional(db, dados)


@router.get("/profissionais/{profissional_id}", response_model=ProfissionalOut, dependencies=[Depends(equipe)])
def detalhar_profissional(profissional_id: int, db: Session = Depends(get_db)):
    return service.obter(db, Profissional, profissional_id, "Profissional")


@router.patch("/profissionais/{profissional_id}", response_model=ProfissionalOut, dependencies=[Depends(so_admin)])
def editar_profissional(profissional_id: int, dados: ProfissionalEdicao, db: Session = Depends(get_db)):
    return service.editar_profissional(db, profissional_id, dados)



@router.post("/unidades/{unidade_id}/desativar", response_model=UnidadeOut, dependencies=[Depends(so_admin)])
def desativar_unidade(unidade_id: int, db: Session = Depends(get_db)):
    return service.desativar_unidade(db, unidade_id)


@router.post("/profissionais/{profissional_id}/desativar", response_model=ProfissionalOut, dependencies=[Depends(so_admin)])
def desativar_profissional(profissional_id: int, db: Session = Depends(get_db)):
    return service.desativar_profissional(db, profissional_id)
