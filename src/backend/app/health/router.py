from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["saude"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "versao": get_settings().versao}
