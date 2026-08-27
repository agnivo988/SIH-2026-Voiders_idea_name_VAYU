from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IndexValue

router = APIRouter(prefix="/api/index", tags=["index"])


@router.get("/current")
def current_index(db: Session = Depends(get_db)) -> dict[str, object]:
    value = db.scalar(select(IndexValue).where(IndexValue.frequency == "daily").order_by(desc(IndexValue.date)))
    if value is None:
        raise HTTPException(404, "Index has not been calculated yet")
    return {"date": value.date, "index_value": float(value.index_value), "daily_change": float(value.percentage_change_daily or 0), "weekly_change": float(value.percentage_change_weekly or 0), "monthly_change": float(value.percentage_change_monthly or 0), "sample_count": value.sample_count, "base_period": value.base_period}


@router.get("/daily")
def daily_index(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    values = db.scalars(select(IndexValue).where(IndexValue.frequency == "daily").order_by(IndexValue.date)).all()
    return [{"date": item.date, "index_value": float(item.index_value), "sample_count": item.sample_count} for item in values]
