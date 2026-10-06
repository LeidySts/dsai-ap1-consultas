from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class UnidadeIn(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    endereco: str = Field(min_length=3, max_length=200)
    cep: str
    telefone: str = Field(min_length=8, max_length=20)
    abertura: time
    fechamento: time
    dias_funcionamento: list[int] = Field(min_length=1)


class UnidadeEdicao(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    endereco: str | None = None
    cep: str | None = None
    telefone: str | None = None
    abertura: time | None = None
    fechamento: time | None = None
    dias_funcionamento: list[int] | None = None


class UnidadeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    endereco: str
    cep: str
    telefone: str
    abertura: time
    fechamento: time
    dias_funcionamento: list[int]
    ativa: bool


class UnidadeResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    endereco: str


class TipoConsultaIn(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    duracao_min: int
    preco_centavos: int = Field(ge=0)


class TipoConsultaEdicao(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=80)
    duracao_min: int | None = None
    preco_centavos: int | None = Field(default=None, ge=0)


class TipoConsultaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    especialidade_id: int
    nome: str
    duracao_min: int
    preco_centavos: int


class EspecialidadeIn(BaseModel):
    nome: str = Field(min_length=2, max_length=80)


class EspecialidadeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipos: list[TipoConsultaOut] = []


class EspecialidadeResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class ProfissionalIn(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    conselho: str = Field(min_length=2, max_length=10)
    registro_numero: str = Field(min_length=1, max_length=20)
    registro_uf: str = Field(min_length=2, max_length=2)
    foto_url: str | None = Field(default=None, max_length=500)
    biografia: str = Field(default="", max_length=500)
    especialidade_ids: list[int] = Field(min_length=1)
    unidade_ids: list[int] = Field(min_length=1)


class ProfissionalEdicao(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    conselho: str | None = None
    registro_numero: str | None = None
    registro_uf: str | None = Field(default=None, min_length=2, max_length=2)
    foto_url: str | None = None
    biografia: str | None = Field(default=None, max_length=500)
    especialidade_ids: list[int] | None = Field(default=None, min_length=1)
    unidade_ids: list[int] | None = Field(default=None, min_length=1)


class ProfissionalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    conselho: str
    registro_numero: str
    registro_uf: str
    registro: str
    foto_url: str | None
    biografia: str
    ativo: bool
    especialidades: list[EspecialidadeResumo]
    unidades: list[UnidadeResumo]
