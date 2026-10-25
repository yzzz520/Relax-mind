import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import init_db
from .routers import admin, auth, capsules, music
from .schemas import HealthResponse
from .seed import seed_database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_database()
    logger.info("Backend startup completed")
    yield


app = FastAPI(
    title="AI Emotion Capsule API",
    version=APP_VERSION,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(capsules.router)
app.include_router(music.router)
app.include_router(admin.router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    """Return validation failures using the shared error envelope."""
    logger.info("Request validation failed: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": "请求参数不合法"},
    )


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
def health():
    """Return backend liveness and version."""
    return HealthResponse(status="UP", version=APP_VERSION)
