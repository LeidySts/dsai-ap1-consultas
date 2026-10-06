from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MarcarIn(BaseModel):
    profissional_id: int
    unidade_id: int
    tipo_consulta_id: int
    inicio: datetime
    forma_pagamento: str = "particular"
    paciente_id: int | None = None  # obrigatório quando quem marca é a recepção


class RemarcarIn(BaseModel):
    inicio: datetime
    unidade_id: int | None = None


class Ref(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class UnidadeRef(Ref):
    endereco: str


class TipoRef(Ref):
    duracao_min: int


class ConsultaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inicio: datetime
    fim: datetime
    status: str
    forma_pagamento: str
    preco_centavos: int
    remarcacoes: int
    paciente: Ref
    profissional: Ref
    unidade: UnidadeRef
    tipo_consulta: TipoRef
    pode_cancelar: bool = False
    pode_remarcar: bool = False


class MinhasConsultas(BaseModel):
    proximas: list[ConsultaOut]
    passadas: list[ConsultaOut]


class HistoricoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    de_status: str | None
    para_status: str
    usuario_id: int
    em: datetime


class PacienteResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    cpf: str | None
