from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class GradeHorario(Base):
    """Faixa semanal de atendimento. Horas no fuso local (America/Sao_Paulo)."""

    __tablename__ = "grade_horarios"
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 0 AND 6", name="ck_grade_dia"),
        CheckConstraint("hora_inicio < hora_fim", name="ck_grade_intervalo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissionais.id", ondelete="CASCADE"), index=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))
    dia_semana: Mapped[int] = mapped_column(Integer)
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fim: Mapped[time] = mapped_column(Time)


class Bloqueio(Base):
    __tablename__ = "bloqueios"
    __table_args__ = (CheckConstraint("inicio < fim", name="ck_bloqueios_intervalo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profissional_id: Mapped[int] = mapped_column(ForeignKey("profissionais.id", ondelete="CASCADE"), index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    motivo: Mapped[str] = mapped_column(String(200))


class Feriado(Base):
    __tablename__ = "feriados"
    __table_args__ = (UniqueConstraint("data", "unidade_id", name="uq_feriados_data_unidade"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[date] = mapped_column(Date, index=True)
    nome: Mapped[str] = mapped_column(String(120))
    # nulo = feriado nacional (vale para todas as unidades)
    unidade_id: Mapped[int | None] = mapped_column(ForeignKey("unidades.id", ondelete="CASCADE"))
