from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Airline

router = APIRouter(prefix="/api/airlines", tags=["airlines"])


@router.get("")
def list_airlines(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return [{"name": item.name, "code": item.code, "active": item.active} for item in db.scalars(select(Airline).order_by(Airline.name))]
