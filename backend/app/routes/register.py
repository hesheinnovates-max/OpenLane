from pathlib import Path
from fastapi import APIRouter , Form , Depends
from fastapi.responses import HTMLResponse
from validations import validate_email, validate_phone, password_strength

from app.db.dependencies import get_db
from app.models.job_seeker import JobSeeker
from app.models.companies import Company

from sqlalchemy.orm import Session
from pwdlib import PasswordHash



router = APIRouter()
password_hasher = PasswordHash.recommended()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/".."/".."/"frontend"/'templates'

# ==================================================
# GET METHODS
# ==================================================
 
@router.get("/company/register",response_class=HTMLResponse)
def business_register():
    return (PAGE/"business_register.html").read_text("utf-8")

@router.get("/job-seeker/register",response_class=HTMLResponse)
def job_seeker_register():
    return (PAGE/"job_seeker_register.html").read_text("utf-8")

# ===================================================
# POST METHODS
# ===================================================

@router.post("/company/register")
def business_register():
    business_name : str = Form(...)
    email : str = Form(...)
    phone : str = Form(...)
    password : str = Form(...)

    if not email or not phone:
        return {"message":"Both Email and Phone required"}

    if validate_email(email) and validate_phone(phone) and password_strength(password):
        pass

@router.post("/job-seeker/register")
def job_seeker_register():
    full_name : str = Form("")
    email : str = Form("")
    phone : str = Form("")
    password : str = Form(...)
    db : Session = Depends(get_db)

    if not email and not phone:
        return {"error":"Email or Phone required"}

    if email:
        true_table = [validate_email(email)[0],password_strength(password)[0]]
        if False in true_table:
            a =  true_table.find(False)
            if a == 0:
                return {"error":f"{validate_email(email)[1]}"}
            else:
                return {"error":f"{password_strength(password)(phone)[1]}"}
            # No Errors:
        else:
            user = db.query(JobSeeker).filter(JobSeeker.email).first()

            if user:
                return {"error":"User already exists"}
            
            password_hash = password_hasher.hash(password)            
            new_user = JobSeeker(
                full_name=full_name,
                email=email,
                password_hash=password_hash,
            )

            db.add(new_user)

            try:
                db.commit()
                db.refresh(new_user)
            except Exception:
                db.rollback()
                raise

            return {"message":"User registered successfully"}
    else:
        true_table = [validate_phone(phone)[0],password_strength(password)[0]]
        if False in true_table:
            a =  true_table.find(False)
            if a == 0:
                return {"error":f"{validate_phone(phone)[1]}"}
            else:
                return {"error":f"{password_strength(password)[1]}"}
        else:
            user = db.query(JobSeeker).filter(JobSeeker.email).first()

            if user:
                return {"error":"User already exists"}
            
            password_hash = password_hasher.hash(password)            
            new_user = JobSeeker(
                full_name=full_name,
                phone=phone,
                password_hash=password_hash,
            )

            db.add(new_user)

            try:
                db.commit()
                db.refresh(new_user)
            except Exception:
                db.rollback()
                raise

            return {"message":"User registered successfully"}