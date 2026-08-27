from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScrapeRun, Source

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
def list_sources(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    sources = db.scalars(select(Source).order_by(Source.name)).all()
    result = []
    for source in sources:
        run = db.scalar(select(ScrapeRun).where(ScrapeRun.source_id == source.id).order_by(ScrapeRun.started_at.desc()))
        result.append({"name": source.name, "type": source.type, "enabled": source.enabled, "is_demo": source.is_demo, "last_successful_run": source.last_successful_run, "last_status": run.status if run else "NOT_RUN"})
    return result
