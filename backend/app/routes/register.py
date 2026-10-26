from pathlib import Path
from fastapi import APIRouter , Form , Depends ,HTTPException
from fastapi.responses import HTMLResponse
from app.routes.validations import validate_the_email, validate_phone, password_strength, normalize_phone, validate_required
from app.routes.sign_in import phone_variants

from app.db.dependencies import get_db
from app.models.job_seeker import JobSeeker
from app.models.companies import Company
from app.models.business import Business

from sqlalchemy import func
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

router = APIRouter()
password_hasher = PasswordHash.recommended()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

PAGE = PROJECT_ROOT/"frontend"/'templates'

# ==================================================
# GET METHODS
# ==================================================

@router.get("/company/register",response_class=HTMLResponse)
def business_register():
    return (PAGE/"company-register.html").read_text("utf-8")

@router.get("/job-seeker/register",response_class=HTMLResponse)
def job_seeker_register_page():
    return (PAGE/"job-seeker-register.html").read_text("utf-8")

# ===================================================
# POST METHODS
# ===================================================

@router.post("/company/register")
def company_register(company_name : str = Form(...)
    ,email : str = Form(...)
    ,phone : str = Form(...)
    ,password : str = Form(...)
    ,confirm_password : str = Form(None)
    ,db : Session = Depends(get_db)):

    company_name = company_name.strip()
    email = email.strip().lower()
    phone = normalize_phone(phone)
    password = password.strip()

    if not email or not phone:
        raise HTTPException(
        status_code=409,
        detail="Both Email and Phone required"
        )

    if confirm_password is not None and confirm_password.strip() != password:
        raise HTTPException(
        status_code=409,
        detail="Passwords do not match"
        )

    true_table = [validate_required(company_name,"Company name",255),validate_the_email(email),validate_phone(phone),password_strength(password)]
    for n in range(len(true_table)):
        if true_table[n] != [True]:
            raise HTTPException(
            status_code=409,
            detail=true_table[n][1]
            )

    user = db.query(Company).filter(func.lower(Company.email)==email).first()

    if user:
        raise HTTPException(
        status_code=409,
        detail="A company with this email already exists"
        )

    user = db.query(Company).filter(Company.phone.in_(phone_variants(phone))).first()

    if user:
        raise HTTPException(
        status_code=409,
        detail="A company with this phone number already exists"
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
        db.flush()
        # Every company starts with a main business , jobs are added under a business
        db.add(Business(company_id=new_user.id,name=company_name,description="Main business"))
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return {"message":"Company registered successfully. Taking you to log in...","redirect":"/company/login"}

@router.post("/job-seeker/register")
def job_seeker_register(full_name : str = Form("")
    ,email : str = Form("")
    ,phone : str = Form("")
    ,password : str = Form(...)
    ,confirm_password : str = Form(None)
    ,db : Session = Depends(get_db)):

    full_name = full_name.strip()
    email = email.strip().lower()
    phone = normalize_phone(phone)
    password = password.strip()


    if not email and not phone:
        raise HTTPException(
        status_code=409,
        detail= "Email or Phone required")

    if confirm_password is not None and confirm_password.strip() != password:
        raise HTTPException(
        status_code=409,
        detail="Passwords do not match"
        )

    true_table = [validate_required(full_name,"Full name",150),password_strength(password)]
    if email:
        true_table.append(validate_the_email(email))
    if phone:
        true_table.append(validate_phone(phone))

    for n in range(len(true_table)):
        if true_table[n] != [True]:
            raise HTTPException(
            status_code=409,
            detail=true_table[n][1]
            )

    if email:
        user = db.query(JobSeeker).filter(func.lower(JobSeeker.email)==email).first()

        if user:
            raise HTTPException(
            status_code=409,
            detail= "User already exists"
            )

    if phone:
        user = db.query(JobSeeker).filter(JobSeeker.phone.in_(phone_variants(phone))).first()

        if user:
            raise HTTPException(
                status_code=409,
                detail="User already exists")

    password_hash = password_hasher.hash(password)
    new_user = JobSeeker(
        full_name=full_name,
        email=email or None,
        phone=phone or None,
        password_hash=password_hash,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return {"message":"User registered successfully. Taking you to log in...","redirect":"/job-seeker/login"}
