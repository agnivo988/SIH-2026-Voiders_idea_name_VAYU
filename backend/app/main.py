from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.api.routes_analytics import router as analytics_router
from app.api.routes_fares import router as fares_router
from app.api.routes_health import router as health_router
from app.api.routes_index import router as index_router
from app.api.routes_routes import router as routes_router
from app.api.routes_admin import router as admin_router
from app.api.routes_airlines import router as airlines_router
from app.api.routes_quality import router as quality_router
from app.api.routes_sources import router as sources_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(index_router)
app.include_router(fares_router)
app.include_router(routes_router)
app.include_router(analytics_router)
app.include_router(airlines_router)
app.include_router(sources_router)
app.include_router(quality_router)
app.include_router(admin_router)


