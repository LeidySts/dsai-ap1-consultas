"""Fábricas e atalhos usados pelos testes do backend."""
from datetime import date
from functools import lru_cache

from app.auth.models import Usuario
from app.core.seguranca import criar_access_token, hash_senha

SENHA = "senha1234"


@lru_cache
def _hash_padrao() -> str:
    return hash_senha(SENHA)


def criar_usuario(db, perfil="paciente", email=None, nome="Fulano de Tal", cpf=None) -> Usuario:
    usuario = Usuario(
        nome=nome,
        email=email or f"{perfil}{db.query(Usuario).count() + 1}@teste.com",
        cpf=cpf,
        data_nascimento=date(1990, 1, 1) if perfil == "paciente" else None,
        telefone="91999990000",
        senha_hash=_hash_padrao(),
        perfil=perfil,
    )
    db.add(usuario)
    db.commit()
    return usuario


def auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {criar_access_token(usuario.id, usuario.perfil)}"}
