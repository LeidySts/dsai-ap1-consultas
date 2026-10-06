"""Relógio e fuso. Banco em UTC; exibição/grade em America/Sao_Paulo."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import get_settings

FUSO_LOCAL = ZoneInfo(get_settings().app_timezone)


class Relogio:
    """Ponto único para "agora"; os testes trocam `atual` para controlar o tempo."""

    atual: datetime | None = None

    @classmethod
    def agora(cls) -> datetime:
        return cls.atual or datetime.now(timezone.utc)


def agora_utc() -> datetime:
    return Relogio.agora()


def para_local(dt: datetime) -> datetime:
    return dt.astimezone(FUSO_LOCAL)
