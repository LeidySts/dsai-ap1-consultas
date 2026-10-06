from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import Usuario
from app.clinicas.models import Profissional, TipoConsulta, Unidade
from app.core.db import Base

STATUS = (
    "marcada",
    "confirmada",
    "em_atendimento",
    "realizada",
    "cancelada_paciente",
    "cancelada_clinica",
    "faltou",
)
# status que ocupam o horário do profissional
STATUS_ATIVOS = ("marcada", "confirmada", "em_atendimento")


class Consulta(Base):
    __tablename__ = "consultas"
    __table_args__ = (
        CheckConstraint(f"status IN {STATUS}", name="ck_consultas_status"),
        CheckConstraint("inicio < fim", name="ck_consultas_intervalo"),
        CheckConstraint("remarcacoes BETWEEN 0 AND 2", name="ck_consultas_remarcacoes"),
        # rede de segurança no banco: mesmo profissional, mesmo início, só uma consulta ativa
        Index(
            "uq_consultas_profissional_inicio_ativa",
            "profissional_id",
            "inicio",
            unique=True,
            postgresql_where=text(f"status IN {STATUS_ATIVOS}"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissionais.id"), index=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), index=True)
    tipo_consulta_id: Mapped[int] = mapped_column(ForeignKey("tipos_consulta.id"))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="marcada")
    forma_pagamento: Mapped[str] = mapped_column(String(20), default="particular")
    preco_centavos: Mapped[int] = mapped_column(Integer)
    remarcacoes: Mapped[int] = mapped_column(Integer, default=0)
    consulta_origem_id: Mapped[int | None] = mapped_column(ForeignKey("consultas.id"))
    criado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    paciente: Mapped[Usuario] = relationship(foreign_keys=[paciente_id], lazy="joined")
    profissional: Mapped[Profissional] = relationship(lazy="joined")
    unidade: Mapped[Unidade] = relationship(lazy="joined")
    tipo_consulta: Mapped[TipoConsulta] = relationship(lazy="joined")


class HistoricoStatus(Base):
    __tablename__ = "historico_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    consulta_id: Mapped[int] = mapped_column(ForeignKey("consultas.id", ondelete="CASCADE"), index=True)
    de_status: Mapped[str | None] = mapped_column(String(20))
    para_status: Mapped[str] = mapped_column(String(20))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
