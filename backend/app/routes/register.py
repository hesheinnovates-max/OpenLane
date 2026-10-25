from pathlib import Path
from fastapi import APIRouter , Form , Depends ,HTTPException
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
JS_DIR = PROJECT_ROOT / "frontend" / "js"

router.mount("/js",StaticFiles(directory=JS_DIR),name="js")
router.mount("/css",StaticFiles(directory=CSS_DIR),name="css")

# ==================================================
# GET METHODS
# ==================================================
 
@router.get("/company/register",response_class=HTMLResponse)
def business_register():
    return (PAGE/"company-register.html").read_text("utf-8")

@router.get("/job-seeker/register",response_class=HTMLResponse)
def job_seeker_register():
    return (PAGE/"job-seeker-register.html").read_text("utf-8")

# ===================================================
# POST METHODS
# ===================================================

@router.post("/company/register")
def company_register(company_name : str = Form(...)
    ,email : str = Form(...)
    ,phone : str = Form(...)
    ,password : str = Form(...)
    ,db : Session = Depends(get_db)):

    company_name = company_name.strip()
    email = email.strip()
    phone = phone.strip()
    password = password.strip()

    if not email or not phone:
        return {"error":"Both Email and Phone required"}

    true_table = [validate_the_email(email),validate_phone(phone),password_strength(password)]
    for n in range(len(true_table)):
        if true_table[n] != [True]:
            raise HTTPException(
            status_code=409,
            detail=true_table[n][1]
            )
    
    user = db.query(Company).filter(Company.company_name==company_name,Company.email==email).first()

    if user:
        raise HTTPException(
        status_code=409,
        detail="Company exists"
        )
    
    password_hash = password_hasher.hash(password)
    new_user = Company(
        company_name=company_name,
        phone=phone,
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

    return {"message":"Company registered successfully"}

@router.post("/job-seeker/register")
def job_seeker_register(full_name : str = Form("")
    ,email : str = Form("")
    ,phone : str = Form("")
    ,password : str = Form(...)
    ,db : Session = Depends(get_db)):

    full_name = full_name.strip()
    email = email.strip()
    phone = phone.strip()
    password = password.strip()


    if not email and not phone:
        raise HTTPException(
        status_code=409,
        detail= "Email or Phone required")

    if email:
        true_table = [validate_the_email(email),password_strength(password)]
        for n in range(len(true_table)):
            if true_table[n] != [True]:
                raise HTTPException(
                status_code=409,
                detail=true_table[n][1]
                )
            
        user = db.query(JobSeeker).filter(JobSeeker.email==email).first()

        if user:
            raise HTTPException(
            status_code=409,
            detail= "User already exists"
            )
        
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
        true_table = [validate_phone(phone),password_strength(password)]
        for n in range(len(true_table)):
            if true_table[n] != [True]:
                raise HTTPException(
                status_code=409,
                detail=true_table[n][1]
                )

        user = db.query(JobSeeker).filter(JobSeeker.email).first()

        if user:
            raise HTTPException(
                status_code=409,
                detail="User already exists")
        
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