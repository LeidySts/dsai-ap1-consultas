from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class FaixaIn(BaseModel):
    unidade_id: int
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fim: time


class FaixaOut(FaixaIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profissional_id: int


class BloqueioIn(BaseModel):
    inicio: datetime
    fim: datetime
    motivo: str = Field(min_length=2, max_length=200)


class BloqueioOut(BloqueioIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profissional_id: int


class FeriadoIn(BaseModel):
    data: date
    nome: str = Field(min_length=2, max_length=120)
    unidade_id: int | None = None


class FeriadoOut(FeriadoIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class HorarioLivre(BaseModel):
    inicio: datetime
    fim: datetime
    unidade_id: int
