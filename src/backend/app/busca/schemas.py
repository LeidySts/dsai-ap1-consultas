from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.clinicas.schemas import TipoConsultaOut


class Opcao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class Filtros(BaseModel):
    especialidades: list[Opcao]
    unidades: list[Opcao]


class ProximoHorario(BaseModel):
    inicio: datetime
    unidade_id: int
    unidade_nome: str


class ResultadoBusca(BaseModel):
    id: int
    nome: str
    foto_url: str | None
    especialidades: list[str]
    unidades: list[str]
    nota_media: float | None
    preco_centavos: int | None
    tipo_consulta_id: int | None
    proximo_horario: ProximoHorario | None
    aviso: str | None


class PaginaBusca(BaseModel):
    itens: list[ResultadoBusca]
    total: int
    pagina: int
    paginas: int


class EspecialidadePublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipos: list[TipoConsultaOut]


class UnidadePublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    endereco: str
    telefone: str


class ProfissionalPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    registro: str
    foto_url: str | None
    biografia: str
    especialidades: list[EspecialidadePublica]
    unidades: list[UnidadePublica]
    nota_media: float | None = None
    total_avaliacoes: int = 0
