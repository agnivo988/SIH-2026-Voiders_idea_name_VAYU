from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    origin: Mapped[str] = mapped_column(String(3), index=True)
    destination: Mapped[str] = mapped_column(String(3), index=True)
    route_code: Mapped[str] = mapped_column(String(7), unique=True, index=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=Decimal("1.0"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Airline(Base):
    __tablename__ = "airlines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[str] = mapped_column(String(30), default="demo")
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    last_successful_run: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FareQuote(Base):
    __tablename__ = "fare_quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    airline_id: Mapped[int] = mapped_column(ForeignKey("airlines.id"), index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    travel_date: Mapped[date] = mapped_column(Date, index=True)
    advance_days: Mapped[int] = mapped_column(Integer, index=True)
    flight_number: Mapped[str] = mapped_column(String(20))
    fare_class: Mapped[str] = mapped_column(String(10), default="Economy")
    base_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    taxes: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    airport_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    convenience_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    other_fees: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)
    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped[Source] = relationship()
    airline: Mapped[Airline] = relationship()
    route: Mapped[Route] = relationship()


class IndexValue(Base):
    __tablename__ = "index_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    frequency: Mapped[str] = mapped_column(String(20), index=True)
    index_value: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    base_period: Mapped[str] = mapped_column(String(100))
    percentage_change_daily: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    percentage_change_weekly: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    percentage_change_monthly: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RouteIndexValue(Base):
    __tablename__ = "route_index_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), index=True)
    index_value: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    representative_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sample_count: Mapped[int] = mapped_column(Integer, default=0)


class BenchmarkValue(Base):
    __tablename__ = "benchmark_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    route: Mapped[str] = mapped_column(String(7), index=True)
    benchmark_value: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    source: Mapped[str] = mapped_column(String(100))


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    records_collected: Mapped[int] = mapped_column(Integer, default=0)
    records_valid: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
