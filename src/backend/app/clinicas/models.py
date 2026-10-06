from datetime import datetime, time

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

profissional_especialidade = Table(
    "profissional_especialidade",
    Base.metadata,
    Column("profissional_id", ForeignKey("profissionais.id", ondelete="CASCADE"), primary_key=True),
    Column("especialidade_id", ForeignKey("especialidades.id", ondelete="CASCADE"), primary_key=True),
)

profissional_unidade = Table(
    "profissional_unidade",
    Base.metadata,
    Column("profissional_id", ForeignKey("profissionais.id", ondelete="CASCADE"), primary_key=True),
    Column("unidade_id", ForeignKey("unidades.id", ondelete="CASCADE"), primary_key=True),
)


class Unidade(Base):
    __tablename__ = "unidades"
    __table_args__ = (CheckConstraint("abertura < fechamento", name="ck_unidades_horario"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    nome_busca: Mapped[str] = mapped_column(String(120), index=True)
    endereco: Mapped[str] = mapped_column(String(200))
    cep: Mapped[str] = mapped_column(String(8))
    telefone: Mapped[str] = mapped_column(String(20))
    abertura: Mapped[time] = mapped_column(Time)
    fechamento: Mapped[time] = mapped_column(Time)
    # 0 = segunda ... 6 = domingo (como date.weekday())
    dias_funcionamento: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    ativa: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Especialidade(Base):
    __tablename__ = "especialidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    nome_busca: Mapped[str] = mapped_column(String(80), index=True)
    tipos: Mapped[list["TipoConsulta"]] = relationship(
        back_populates="especialidade", order_by="TipoConsulta.duracao_min", lazy="selectin"
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TipoConsulta(Base):
    __tablename__ = "tipos_consulta"
    __table_args__ = (
        CheckConstraint("duracao_min BETWEEN 15 AND 120 AND duracao_min % 5 = 0", name="ck_tipos_duracao"),
        CheckConstraint("preco_centavos >= 0", name="ck_tipos_preco"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    especialidade_id: Mapped[int] = mapped_column(ForeignKey("especialidades.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(80))
    duracao_min: Mapped[int] = mapped_column(Integer)
    preco_centavos: Mapped[int] = mapped_column(Integer)
    especialidade: Mapped[Especialidade] = relationship(back_populates="tipos")


class Profissional(Base):
    __tablename__ = "profissionais"
    __table_args__ = (
        UniqueConstraint("conselho", "registro_numero", "registro_uf", name="uq_profissionais_registro"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    nome: Mapped[str] = mapped_column(String(120))
    nome_busca: Mapped[str] = mapped_column(String(120), index=True)
    conselho: Mapped[str] = mapped_column(String(10))
    registro_numero: Mapped[str] = mapped_column(String(20))
    registro_uf: Mapped[str] = mapped_column(String(2))
    foto_url: Mapped[str | None] = mapped_column(String(500))
    biografia: Mapped[str] = mapped_column(Text, default="")
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    especialidades: Mapped[list[Especialidade]] = relationship(
        secondary=profissional_especialidade, order_by=Especialidade.nome, lazy="selectin"
    )
    unidades: Mapped[list[Unidade]] = relationship(secondary=profissional_unidade, order_by=Unidade.nome, lazy="selectin")

    @property
    def registro(self) -> str:
        return f"{self.conselho} {self.registro_numero}/{self.registro_uf}"
