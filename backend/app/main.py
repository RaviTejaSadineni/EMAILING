from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.redis_client import close_redis_client, get_redis_client
from app.routers import auth, classification, contracts, health, imports, lifecycle, stakeholders, threads, ws

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        redis = await get_redis_client()
        await redis.ping()
    except Exception:
        redis = None
    yield
    if redis is not None:
        await close_redis_client()


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(imports.router)
app.include_router(ws.router)
app.include_router(classification.router)
app.include_router(threads.router)
app.include_router(contracts.router)
app.include_router(stakeholders.router)
app.include_router(lifecycle.router)
