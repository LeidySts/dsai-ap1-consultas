import re
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import TokenRenovacao, Usuario
from app.auth.schemas import CadastroIn
from app.core.erros import Conflito, ContaBloqueada, NaoAutenticado, RegraViolada
from app.core.seguranca import criar_access_token, hash_senha, hash_token, novo_refresh_token, verificar_senha
from app.core.tempo import agora_utc

MAX_TENTATIVAS = 5
TEMPO_BLOQUEIO = timedelta(minutes=15)
MSG_BLOQUEADA = "Conta bloqueada por excesso de tentativas. Tente novamente em 15 minutos."
MSG_CREDENCIAIS = "E-mail ou senha incorretos."
MSG_SESSAO = "Sessão expirada. Entre novamente."


def somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def cpf_valido(cpf: str) -> bool:
    cpf = somente_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10) % 11 % 10 != int(cpf[tamanho]):
            return False
    return True


def validar_senha(senha: str) -> None:
    if len(senha) < 8 or not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise RegraViolada("A senha precisa ter no mínimo 8 caracteres, com letras e números.")


def cadastrar_paciente(db: Session, dados: CadastroIn) -> Usuario:
    cpf = somente_digitos(dados.cpf)
    if not cpf_valido(cpf):
        raise RegraViolada("CPF inválido.")
    validar_senha(dados.senha)
    email = dados.email.lower()
    if db.scalar(select(Usuario.id).where(Usuario.email == email)):
        raise Conflito("Este e-mail já está cadastrado.")
    if db.scalar(select(Usuario.id).where(Usuario.cpf == cpf)):
        raise Conflito("Este CPF já está cadastrado.")
    usuario = Usuario(
        nome=dados.nome.strip(),
        email=email,
        cpf=cpf,
        data_nascimento=dados.data_nascimento,
        telefone=dados.telefone,
        senha_hash=hash_senha(dados.senha),
        perfil="paciente",
    )
    db.add(usuario)
    db.commit()
    return usuario


def login(db: Session, email: str, senha: str) -> tuple[str, str]:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email.lower()))
    if usuario is None or not usuario.ativo:
        raise NaoAutenticado(MSG_CREDENCIAIS)
    agora = agora_utc()
    if usuario.bloqueado_ate and usuario.bloqueado_ate > agora:
        raise ContaBloqueada(MSG_BLOQUEADA)
    if not verificar_senha(senha, usuario.senha_hash):
        usuario.tentativas_falhas += 1
        bloqueou = usuario.tentativas_falhas >= MAX_TENTATIVAS
        if bloqueou:
            usuario.tentativas_falhas = 0
            usuario.bloqueado_ate = agora + TEMPO_BLOQUEIO
        db.commit()
        raise ContaBloqueada(MSG_BLOQUEADA) if bloqueou else NaoAutenticado(MSG_CREDENCIAIS)
    usuario.tentativas_falhas = 0
    usuario.bloqueado_ate = None
    refresh, refresh_hash, expira = novo_refresh_token()
    db.add(TokenRenovacao(usuario_id=usuario.id, token_hash=refresh_hash, expira_em=expira))
    db.commit()
    return criar_access_token(usuario.id, usuario.perfil), refresh


def _buscar_token(db: Session, refresh_token: str) -> TokenRenovacao | None:
    return db.scalar(select(TokenRenovacao).where(TokenRenovacao.token_hash == hash_token(refresh_token)))


def renovar(db: Session, refresh_token: str) -> str:
    registro = _buscar_token(db, refresh_token)
    if registro is None or registro.revogado_em is not None or registro.expira_em <= agora_utc():
        raise NaoAutenticado(MSG_SESSAO)
    usuario = db.get(Usuario, registro.usuario_id)
    if usuario is None or not usuario.ativo:
        raise NaoAutenticado(MSG_SESSAO)
    return criar_access_token(usuario.id, usuario.perfil)


def logout(db: Session, usuario: Usuario, refresh_token: str) -> None:
    registro = _buscar_token(db, refresh_token)
    if registro is not None and registro.usuario_id == usuario.id and registro.revogado_em is None:
        registro.revogado_em = agora_utc()
        db.commit()
