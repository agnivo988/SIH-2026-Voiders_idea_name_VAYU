from fastapi import APIRouter, Header, HTTPException

from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_key(x_admin_api_key: str | None) -> None:
    if not x_admin_api_key or x_admin_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin API key")


@router.post("/run-collection")
def run_collection(x_admin_api_key: str | None = Header(default=None)) -> dict[str, str]:
    require_key(x_admin_api_key)
    return {"status": "queued", "message": "Collection job queued; live adapters remain disabled by default"}


@router.post("/recalculate-index")
def recalculate_index(x_admin_api_key: str | None = Header(default=None)) -> dict[str, str]:
    require_key(x_admin_api_key)
    return {"status": "queued", "message": "Index recalculation job queued"}
