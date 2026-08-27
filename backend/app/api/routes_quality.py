from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FareQuote, ScrapeRun

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])


@router.get("")
def data_quality(db: Session = Depends(get_db)) -> dict[str, int | float]:
    total = db.scalar(select(func.count(FareQuote.id))) or 0
    valid = db.scalar(select(func.count(FareQuote.id)).where(FareQuote.available.is_(True))) or 0
    outliers = db.scalar(select(func.count(FareQuote.id)).where(FareQuote.is_outlier.is_(True))) or 0
    failures = db.scalar(select(func.sum(ScrapeRun.error_count))) or 0
    quality = round(valid / total * 100, 2) if total else 0.0
    return {"total_collected": total, "valid": valid, "invalid": total - valid, "outliers": outliers, "sold_out": total - valid, "missing": 0, "scrape_failures": failures, "quality_score": quality}
