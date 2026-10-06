import hashlib
import secrets
from collections.abc import Callable
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.erros import NaoAutenticado, Proibido
from app.core.tempo import agora_utc

DURACAO_ACCESS = timedelta(minutes=30)
DURACAO_REFRESH = timedelta(days=7)
_bearer = HTTPBearer(auto_error=False)


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def criar_access_token(usuario_id: int, perfil: str) -> str:
    agora = agora_utc()
    dados = {
        "sub": str(usuario_id),
        "perfil": perfil,
        "iat": int(agora.timestamp()),
        "exp": int((agora + DURACAO_ACCESS).timestamp()),
        "tipo": "access",
    }
    return jwt.encode(dados, get_settings().jwt_secret, algorithm="HS256")


def ler_access_token(token: str) -> dict:
    try:
        # exp e iat são conferidos com o relógio da aplicação (controlável nos testes)
        dados = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"], options={"verify_exp": False, "verify_iat": False})
    except jwt.PyJWTError as exc:
        raise NaoAutenticado("Sessão inválida. Entre novamente.") from exc
    if dados.get("tipo") != "access" or dados["exp"] <= agora_utc().timestamp():
        raise NaoAutenticado("Sessão expirada. Entre novamente.")
    return dados


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def novo_refresh_token() -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(48)
    return token, hash_token(token), agora_utc() + DURACAO_REFRESH


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)
):
    from app.auth.models import Usuario

    if credenciais is None:
        raise NaoAutenticado("É preciso entrar para acessar esta página.")
    dados = ler_access_token(credenciais.credentials)
    usuario = db.get(Usuario, int(dados["sub"]))
    if usuario is None or not usuario.ativo:
        raise NaoAutenticado("Sessão inválida. Entre novamente.")
    return usuario


def exige_perfil(*perfis: str) -> Callable:
    def dependencia(usuario=Depends(usuario_atual)):
        if usuario.perfil not in perfis:
            raise Proibido("Seu perfil não tem permissão para esta ação.")
        return usuario

    return dependencia
