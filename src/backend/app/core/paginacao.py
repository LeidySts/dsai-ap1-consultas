from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    itens: list[T]
    total: int
    pagina: int
    paginas: int


def paginar(db: Session, consulta: Select, pagina: int, por_pagina: int) -> dict:
    pagina = max(pagina, 1)
    total = db.scalar(select(func.count()).select_from(consulta.order_by(None).subquery())) or 0
    itens = db.scalars(consulta.limit(por_pagina).offset((pagina - 1) * por_pagina)).unique().all()
    return {"itens": itens, "total": total, "pagina": pagina, "paginas": max(ceil(total / por_pagina), 1)}
