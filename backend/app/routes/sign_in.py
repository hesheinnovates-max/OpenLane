from pathlib import Path
from fastapi import APIRouter , Form , Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.routes.validations import validate_email, validate_phone, password_strength

from app.db.dependencies import get_db
from app.models.job_seeker import JobSeeker
from app.models.companies import Company

from sqlalchemy.orm import Session
from pwdlib import PasswordHash

router = APIRouter()
password_hasher = PasswordHash.recommended()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

PAGE = PROJECT_ROOT/"frontend"/'templates'
CSS_DIR = PROJECT_ROOT/"frontend"/'css'

router.mount("/css",StaticFiles(directory=CSS_DIR),name="css")

@router.get("/job-seeker/login",response_class=HTMLResponse)
def job_seeker_login():
    return (PAGE/"job-seeker-login.html").read_text(encoding="utf-8")

@router.get("/company/login",response_class=HTMLResponse)
def company_login():
    return (PAGE/"company-login.html").read_text(encoding="utf-8")

# ===========================================================
# --------- Sign In Functionality ---------------------------
# ===========================================================


