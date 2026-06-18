import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import history, review
from app.services.review_service import ENGINE_NAME, ENGINE_VERSION

_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
_extra = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
_origins = _default_origins + ([_extra] if _extra else [])


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CodeReview",
    description="Multi-language static code review platform",
    version=ENGINE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review.router)
app.include_router(history.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "CodeReview"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "CodeReview",
        "engine": {
            "name": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "offline": True,
            "languages": ["python", "javascript", "typescript", "java", "cpp"],
        },
    }
