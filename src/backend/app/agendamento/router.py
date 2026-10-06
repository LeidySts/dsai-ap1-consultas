from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.agenda.service import obter_profissional
from app.agendamento import service
from app.agendamento.schemas import (
    ConsultaOut,
    HistoricoOut,
    MarcarIn,
    MinhasConsultas,
    PacienteResumo,
    RemarcarIn,
)
from app.core.db import get_db
from app.core.erros import Proibido
from app.core.seguranca import exige_perfil, usuario_atual
from app.core.tempo import FUSO_LOCAL

router = APIRouter(tags=["agendamento"])
quem_marca = exige_perfil("paciente", "recepcao", "admin")
equipe = exige_perfil("recepcao", "admin")


@router.post("/consultas", response_model=ConsultaOut, status_code=status.HTTP_201_CREATED)
def marcar(dados: MarcarIn, usuario=Depends(quem_marca), db: Session = Depends(get_db)):
    return service.com_permissoes(service.marcar(db, usuario, dados), usuario)


@router.get("/consultas/minhas", response_model=MinhasConsultas)
def minhas(usuario=Depends(exige_perfil("paciente")), db: Session = Depends(get_db)):
    return service.minhas(db, usuario)


@router.get("/consultas/{consulta_id}", response_model=ConsultaOut)
def detalhar(consulta_id: int, usuario=Depends(usuario_atual), db: Session = Depends(get_db)):
    return service.com_permissoes(service.obter_consulta(db, consulta_id, usuario), usuario)


@router.post("/consultas/{consulta_id}/cancelar", response_model=ConsultaOut)
def cancelar(consulta_id: int, usuario=Depends(quem_marca), db: Session = Depends(get_db)):
    consulta = service.obter_consulta(db, consulta_id, usuario)
    return service.com_permissoes(service.cancelar(db, consulta, usuario), usuario)


@router.post("/consultas/{consulta_id}/remarcar", response_model=ConsultaOut, status_code=status.HTTP_201_CREATED)
def remarcar(consulta_id: int, dados: RemarcarIn, usuario=Depends(quem_marca), db: Session = Depends(get_db)):
    consulta = service.obter_consulta(db, consulta_id, usuario)
    nova = service.remarcar(db, consulta, usuario, dados.inicio, dados.unidade_id)
    return service.com_permissoes(nova, usuario)


@router.get("/consultas/{consulta_id}/historico", response_model=list[HistoricoOut])
def historico(consulta_id: int, usuario=Depends(usuario_atual), db: Session = Depends(get_db)):
    return service.historico(db, service.obter_consulta(db, consulta_id, usuario))


@router.get("/pacientes", response_model=list[PacienteResumo], dependencies=[Depends(equipe)])
def pacientes(q: str = "", db: Session = Depends(get_db)):
    return service.buscar_pacientes(db, q)


@router.get("/profissionais/{profissional_id}/agenda", response_model=list[ConsultaOut])
def agenda(
    profissional_id: int,
    de: date,
    ate: date,
    usuario=Depends(exige_perfil("profissional", "recepcao", "admin")),
    db: Session = Depends(get_db),
):
    profissional = obter_profissional(db, profissional_id)
    if usuario.perfil == "profissional" and profissional.usuario_id != usuario.id:
        raise Proibido("Você só pode ver a sua própria agenda.")
    inicio = datetime.combine(de, time.min, FUSO_LOCAL)
    fim = datetime.combine(ate + timedelta(days=1), time.min, FUSO_LOCAL)
    return [service.com_permissoes(c, usuario) for c in service.agenda_profissional(db, profissional_id, inicio, fim)]
