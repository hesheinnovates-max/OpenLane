from pathlib import Path
from fastapi import APIRouter , Form , Depends , HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.routes.validations import validate_the_email, validate_phone, password_strength

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
# Find the frontend JavaScript directory
JS_DIR = PROJECT_ROOT / "frontend" / "js"

# Serve JavaScript files
router.mount("/js",StaticFiles(directory=JS_DIR),name="js")

@router.get("/job-seeker/login",response_class=HTMLResponse)
def job_seeker_login():
    return (PAGE/"job-seeker-login.html").read_text(encoding="utf-8")

@router.get("/company/login",response_class=HTMLResponse)
def company_login():
    return (PAGE/"company-login.html").read_text(encoding="utf-8")

# ===========================================================
# --------- Sign In Functionality ---------------------------
# ===========================================================

@router.post("/company/login")
def company_login(identifier : str = Form(...),
    password: str = Form(...),
    db : Session = Depends(get_db)):

    identifier = identifier.strip()
    password = password.strip()

    email = ""
    phone = ""
    if "@" in identifier:
        email = identifier
        validate = validate_the_email(email)
        if len(validate) == 2:
            raise HTTPException(
            status_code=409,
            detail= validate[1]
            )
    else:
        phone = identifier
        validate = validate_phone(phone)
        if len(validate) == 2:
            raise HTTPException(
            status_code=409,
            detail= validate[1]
            )

    if phone:
        user_data = db.query(Company).filter(Company.phone == phone).first()
        if not(user_data):
            raise HTTPException (
                status_code=409,
                detail = "No such user , create an account"
            )
        else:
            password_hash = password_hasher.hash(password)
            if password_hash == user_data.password_hash:
                return {"message":"Success"}
            else:
                raise HTTPException (
                status_code=409,
                detail = "Incorrect logins"
            )   
    else:

        user_data = db.query(Company).filter(Company.email == email).first()
        if not(user_data):
            raise HTTPException (
                status_code=409,
                detail = "No such user , create an account"
            )
        else:
            password_hash = password_hasher.hash(password)
            if password_hash == user_data.password_hash:
                return {"message":"Success"}
            else:
                raise HTTPException (
                status_code=409,
                detail = "Incorrect logins"
                )
            
@router.post("/job-seeker/login")
def job_seeker_login(identifier : str = Form(...),
    password: str = Form(...),
    db : Session = Depends(get_db)):

    identifier = identifier.strip()
    password = password.strip()

    email = ""
    phone = ""
    if "@" in identifier:
        email = identifier
        validate = validate_the_email(email)
        if len(validate) == 2:
            raise HTTPException(
            status_code=409,
            detail= validate[1]
            )
    else:
        phone = identifier
        validate = validate_phone(phone)
        if len(validate) == 2:
            raise HTTPException(
            status_code=409,
            detail= validate[1]
            )
        
    if phone:
        user_data = db.query(JobSeeker).filter(JobSeeker.phone == phone).first()
        if not(user_data):
            raise HTTPException (
                status_code=409,
                detail = "No such user , create an account"
            )
        else:
            password_hash = password_hasher.hash(password)
            if password_hash == user_data.password_hash:
                return {"message":"Success"}
            else:
                raise HTTPException (
                status_code=409,
                detail = "Incorrect logins"
            )   
    else:
        user_data = db.query(JobSeeker).filter(JobSeeker.email == email).first()
        if not(user_data):
            raise HTTPException (
                status_code=409,
                detail = "No such user , create an account"
            )
        else:
            password_hash = password_hasher.hash(password)
            if password_hash == user_data.password_hash:
                return {"message":"Success"}
            else:
                raise HTTPException (
                status_code=409,
                detail = "Incorrect logins"
                )

