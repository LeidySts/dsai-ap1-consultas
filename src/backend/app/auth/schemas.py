from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CadastroIn(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    cpf: str
    data_nascimento: date
    telefone: str = Field(min_length=8, max_length=20)
    senha: str


class LoginIn(BaseModel):
    email: EmailStr
    senha: str


class RenovarIn(BaseModel):
    refresh_token: str


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expira_em_segundos: int


class AccessOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_em_segundos: int


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    perfil: str
    telefone: str | None = None
    data_nascimento: date | None = None
