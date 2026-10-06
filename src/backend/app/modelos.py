"""Importa os modelos de todos os módulos para o Alembic e para os testes."""
from app.auth import models as auth_models  # noqa: F401
from app.clinicas import models as clinicas_models  # noqa: F401
from app.core.db import Base

__all__ = ["Base"]
