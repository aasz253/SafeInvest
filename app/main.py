import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.v1 import auth, packages, deposits, earnings, referrals, feedback, admin, gifts, deposit_requests

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Mobile-first investment platform with daily earnings",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(packages.router, prefix="/api/v1")
app.include_router(deposits.router, prefix="/api/v1")
app.include_router(earnings.router, prefix="/api/v1")
app.include_router(referrals.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(gifts.router, prefix="/api/v1")
app.include_router(deposit_requests.router, prefix="/api/v1")


uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    from app.seed import run_seed
    run_seed()


@app.get("/")
def root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
