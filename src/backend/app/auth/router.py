from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.schemas import AccessOut, CadastroIn, LoginIn, RenovarIn, TokensOut, UsuarioOut
from app.core.db import get_db
from app.core.seguranca import DURACAO_ACCESS, usuario_atual

router = APIRouter(prefix="/auth", tags=["autenticacao"])
SEGUNDOS_ACCESS = int(DURACAO_ACCESS.total_seconds())


@router.post("/cadastro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def cadastro(dados: CadastroIn, db: Session = Depends(get_db)):
    return service.cadastrar_paciente(db, dados)


@router.post("/login", response_model=TokensOut)
def login(dados: LoginIn, db: Session = Depends(get_db)):
    access, refresh = service.login(db, dados.email, dados.senha)
    return TokensOut(access_token=access, refresh_token=refresh, expira_em_segundos=SEGUNDOS_ACCESS)


@router.post("/renovar", response_model=AccessOut)
def renovar(dados: RenovarIn, db: Session = Depends(get_db)):
    return AccessOut(access_token=service.renovar(db, dados.refresh_token), expira_em_segundos=SEGUNDOS_ACCESS)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(dados: RenovarIn, usuario=Depends(usuario_atual), db: Session = Depends(get_db)):
    service.logout(db, usuario, dados.refresh_token)


@router.get("/eu", response_model=UsuarioOut)
def eu(usuario=Depends(usuario_atual)):
    return usuario
