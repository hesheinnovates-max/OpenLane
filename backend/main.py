from pathlib import Path

from fastapi import FastAPI , Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app.db.dependencies import get_db

# --------- Include all the routes --------- 
from app.routes import sign_in
from app.routes import job_seekers
from app.routes import companies
from app.routes import register

app = FastAPI(title="OpenLane ApI",description="API for OpenLane Platform",version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------- Include the routes ------------
app.include_router(sign_in.router)
app.include_router(job_seekers.router)
app.include_router(companies.router)
app.include_router(register.router)


# Find project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/"frontend"/'templates'


@app.get("/",response_class=HTMLResponse)
def root():
    return (PAGE/"openlane_homepage.html").read_text(encoding="utf-8")

@app.get("/db-check",response_class=HTMLResponse)
def db_check(db:Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database_connected": result.scalar() == 1}

