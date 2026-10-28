import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from app.database import engine, Base
from app.routers import accounts, transfers

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transaction Ledger API",
    description="Atomic banking ledger API with row-level locks and full ACID support",
    version="1.0.0",
)

# Absolute path to the static folder to prevent Windows relative path lookup issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    return FileResponse(INDEX_PATH)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

app.include_router(accounts.router, prefix="/api/v1")
app.include_router(transfers.router, prefix="/api/v1")