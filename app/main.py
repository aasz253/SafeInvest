import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.v1 import auth, packages, deposits, earnings, referrals, feedback, admin, gifts, deposit_requests, withdrawals

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
app.include_router(withdrawals.router, prefix="/api/v1")

uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
try:
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
except Exception:
    pass

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if not os.path.exists(frontend_dir):
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

try:
    css_dir = os.path.join(frontend_dir, "css")
    js_dir = os.path.join(frontend_dir, "js")
    images_dir = os.path.join(frontend_dir, "images")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    if os.path.exists(images_dir):
        app.mount("/images", StaticFiles(directory=images_dir), name="images")
except Exception:
    pass


@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        from app.seed import run_seed
        run_seed()
    except Exception as e:
        print(f"Startup error (non-fatal): {e}")


@app.middleware("http")
async def serve_spa(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404 and not request.url.path.startswith("/api") and not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi") and not request.url.path.startswith("/uploads") and not request.url.path.startswith("/css") and not request.url.path.startswith("/js") and not request.url.path.startswith("/images"):
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return response


@app.get("/favicon.ico")
def favicon():
    return JSONResponse(status_code=204, content=None)


@app.get("/health")
def health():
    return {"status": "healthy"}
