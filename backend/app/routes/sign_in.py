import secrets
from pathlib import Path
from fastapi import APIRouter , Form , Depends , HTTPException , Request
from fastapi.responses import HTMLResponse , RedirectResponse , JSONResponse
from app.routes.validations import validate_the_email, validate_phone, password_strength, normalize_phone

from app.db.dependencies import get_db
from app.models.job_seeker import JobSeeker
from app.models.companies import Company
from app.models.reset_password import PasswordReset , RESET_CODE_MINUTES , MAX_RESET_ATTEMPTS
from app.services.auth import login_response , clear_session , read_session , ROLE_COMPANY , ROLE_JOB_SEEKER
from app.services.notify import send_reset_code , show_reset_code

from sqlalchemy import func , or_ , literal_column
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

router = APIRouter()
password_hasher = PasswordHash.recommended()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

PAGE = PROJECT_ROOT/"frontend"/'templates'

ACCOUNT_TYPES = [ROLE_JOB_SEEKER,ROLE_COMPANY]

@router.get("/job-seeker/login",response_class=HTMLResponse)
def job_seeker_login_page(request : Request):
    session = read_session(request)
    if session and session["role"] == ROLE_JOB_SEEKER:
        return RedirectResponse("/job-seeker/dashboard",status_code=303)
    return (PAGE/"job-seeker-login.html").read_text(encoding="utf-8")

@router.get("/company/login",response_class=HTMLResponse)
def company_login_page(request : Request):
    session = read_session(request)
    if session and session["role"] == ROLE_COMPANY:
        return RedirectResponse("/company/dashboard",status_code=303)
    return (PAGE/"company-login.html").read_text(encoding="utf-8")

@router.get("/forgot-password",response_class=HTMLResponse)
def forgot_password_page():
    return (PAGE/"token-account.html").read_text("utf-8")

@router.get("/password-reset",response_class=HTMLResponse)
def password_reset_page():
    return (PAGE/"reset-password.html").read_text("utf-8")

@router.get("/logout")
def logout():
    response = RedirectResponse("/",status_code=303)
    return clear_session(response)

@router.get("/api/me")
def me(request : Request,db : Session = Depends(get_db)):
    session = read_session(request)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Not logged in"
        )
    if session["role"] == ROLE_COMPANY:
        user = db.query(Company).filter(Company.id == session["user_id"]).first()
        if user:
            return {"role":ROLE_COMPANY,"id":user.id,"name":user.company_name,"email":user.email,"phone":user.phone}
    else:
        user = db.query(JobSeeker).filter(JobSeeker.id == session["user_id"]).first()
        if user:
            return {"role":ROLE_JOB_SEEKER,"id":user.id,"name":user.full_name,"email":user.email,"phone":user.phone}
    raise HTTPException(
        status_code=401,
        detail="Not logged in"
    )

# ===========================================================
# --------- Helpers -----------------------------------------
# ===========================================================

def find_account(db,account_type,email,phone):
    # Find the company or job seeker that owns this email / phone
    model = Company if account_type == ROLE_COMPANY else JobSeeker
    if email:
        return db.query(model).filter(func.lower(model.email) == email.lower()).first()
    return db.query(model).filter(model.phone.in_(phone_variants(phone))).first()

def phone_variants(phone):
    # 0821234567 and +27821234567 are the same South African number
    variants = [phone]
    if phone.startswith("+27"):
        variants.append("0" + phone[3:])
    elif phone.startswith("0"):
        variants.append("+27" + phone[1:])
    return variants

def split_detail(detail):
    # Work out if the user typed an email or a phone number
    detail = detail.strip()
    if "@" in detail:
        validate = validate_the_email(detail)
        if len(validate) == 2:
            raise HTTPException(
            status_code=409,
            detail= validate[1]
            )
        return detail.lower() , ""
    validate = validate_phone(detail)
    if len(validate) == 2:
        raise HTTPException(
        status_code=409,
        detail= validate[1]
        )
    return "" , normalize_phone(detail)

def check_account_type(account_type):
    account_type = account_type.strip().replace("-","_")
    if account_type not in ACCOUNT_TYPES:
        raise HTTPException(
            status_code=409,
            detail="Choose if this is a Job Seeker or a Company account"
        )
    return account_type

# ===========================================================
# --------- Password Reset Functionality --------------------
# ===========================================================

@router.post("/forgot-password")
def forgot_password(detail : str = Form(...),
    account_type : str = Form(ROLE_JOB_SEEKER),
    db: Session = Depends(get_db)):

    account_type = check_account_type(account_type)
    email , phone = split_detail(detail)

    user = find_account(db,account_type,email,phone)
    if not user:
        raise HTTPException (
            status_code=409,
            detail = "Enter correct account details"
        )

    # 6 digit code , only the hash is stored in the database
    reset_code = f"{secrets.randbelow(1000000):06d}"

    if email:
        old_one = db.query(PasswordReset).filter(PasswordReset.account_type==account_type,PasswordReset.email==email).first()
    else:
        old_one = db.query(PasswordReset).filter(PasswordReset.account_type==account_type,PasswordReset.phone==phone).first()

    if old_one:
        old_one.reset_code = password_hasher.hash(reset_code)
        old_one.attempts = 0
        old_one.used = False
        old_one.created_at = func.now()
    else:
        new_reset = PasswordReset(
            account_type=account_type,
            email=email or None,
            phone=phone or None,
            reset_code=password_hasher.hash(reset_code),
        )
        db.add(new_reset)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    sent_by_email = send_reset_code(email or phone,reset_code)

    message = "A reset code has been sent. It expires in 5 minutes."
    if not sent_by_email:
        message = "A reset code has been created. It expires in 5 minutes."
    if show_reset_code():
        message += f" (Development mode code: {reset_code})"

    return {
        "message": message,
        "redirect": f"/password-reset?detail={email or phone}&type={account_type}",
    }

@router.post("/password-reset")
def password_reset(detail: str = Form(...),
        account_type : str = Form(ROLE_JOB_SEEKER),
        reset_token : str = Form(...),
        new_password: str = Form(...),
        confirm_password: str = Form(None),
        db: Session = Depends(get_db)):

    account_type = check_account_type(account_type)
    email , phone = split_detail(detail)
    reset_token = reset_token.strip()
    password = new_password.strip()

    if confirm_password is not None and confirm_password.strip() != password:
        raise HTTPException (
            status_code=409,
            detail="Passwords do not match")

    validate = password_strength(password)
    if len(validate) == 2:
        raise HTTPException (
            status_code=409,
            detail=validate[1])

    if email:
        user = db.query(PasswordReset).filter(PasswordReset.account_type==account_type,PasswordReset.email==email).first()
    else:
        user = db.query(PasswordReset).filter(PasswordReset.account_type==account_type,PasswordReset.phone==phone).first()

    if not user:
        raise HTTPException (
            status_code=409,
            detail="No reset code for this account, request a new code")

    if user.used:
        raise HTTPException (
            status_code=409,
            detail="This code was already used, request a new code")

    if user.attempts >= MAX_RESET_ATTEMPTS:
        raise HTTPException (
            status_code=409,
            detail="Too many attempts, request a new code")

    # The database decides if the code expired , same func.now() clock used for created_at
    still_valid = db.query(PasswordReset).filter(
        PasswordReset.id == user.id,
        PasswordReset.created_at >= func.now() - literal_column(f"interval '{RESET_CODE_MINUTES} minutes'")
    ).first()

    if not still_valid:
        raise HTTPException (
            status_code=409,
            detail="The code has expired, request a new code")

    if not password_hasher.verify(reset_token,user.reset_code):
        user.attempts += 1
        db.commit()
        left = MAX_RESET_ATTEMPTS - user.attempts
        if left <= 0:
            raise HTTPException (
                status_code=409,
                detail="Too many attempts, request a new code")
        raise HTTPException (
            status_code=409,
            detail=f"Enter the correct code ({left} attempts left)")

    account = find_account(db,account_type,email,phone)
    if not account:
        raise HTTPException (
            status_code=409,
            detail="No such account")

    account.password_hash = password_hasher.hash(password)
    user.used = True
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    login_page = "/company/login" if account_type == ROLE_COMPANY else "/job-seeker/login"
    return {"message":"Password changed. You can now log in.","redirect":login_page}

# ===========================================================
# --------- Sign In Functionality ---------------------------
# ===========================================================

@router.post("/company/login")
def company_login(identifier : str = Form(...),
    password: str = Form(...),
    db : Session = Depends(get_db)):

    identifier = identifier.strip()
    password = password.strip()

    email , phone = split_detail(identifier)

    user_data = find_account(db,ROLE_COMPANY,email,phone)
    if not(user_data):
        raise HTTPException (
            status_code=409,
            detail = "No such user , create an account"
        )

    if password_hasher.verify(password,user_data.password_hash):
        return login_response(user_data.id,ROLE_COMPANY,"Success","/company/dashboard")
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

    email , phone = split_detail(identifier)

    user_data = find_account(db,ROLE_JOB_SEEKER,email,phone)
    if not(user_data):
        raise HTTPException (
            status_code=409,
            detail = "No such user , create an account"
        )

    if not user_data.is_active:
        raise HTTPException (
            status_code=409,
            detail = "This account is disabled"
        )

    if password_hasher.verify(password,user_data.password_hash):
        return login_response(user_data.id,ROLE_JOB_SEEKER,"Success","/job-seeker/dashboard")
    else:
        raise HTTPException (
        status_code=409,
        detail = "Incorrect logins"
        )
