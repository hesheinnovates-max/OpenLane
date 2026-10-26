import os
import time
import secrets

import jwt
from dotenv import load_dotenv
from fastapi import Request , Depends , HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.job_seeker import JobSeeker
from app.models.companies import Company

load_dotenv()

SESSION_COOKIE = "openlane_session"
SESSION_SECONDS = 60 * 60 * 8  # Stay logged in for 8 hours
ALGORITHM = "HS256"

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Sessions still work, but everyone is logged out when the server restarts
    print("WARNING: SECRET_KEY is not set in the .env file. Using a temporary key.")
    SECRET_KEY = secrets.token_urlsafe(48)

# Use secure cookies when the site runs on HTTPS (set COOKIE_SECURE=true in production)
COOKIE_SECURE = os.getenv("COOKIE_SECURE","false").lower() == "true"

ROLE_COMPANY = "company"
ROLE_JOB_SEEKER = "job_seeker"

# ==========================================================
# Session token helpers
# ==========================================================

def create_session_token(user_id,role):
    issued_at = int(time.time())
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": issued_at,
        "exp": issued_at + SESSION_SECONDS,
    }
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def read_session(request : Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return {"user_id": int(payload["sub"]),"role": payload["role"]}
    except (jwt.PyJWTError,KeyError,ValueError):
        return None

def login_response(user_id,role,message,redirect):
    response = JSONResponse({"message":message,"redirect":redirect})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(user_id,role),
        max_age=SESSION_SECONDS,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    return response

def clear_session(response):
    response.delete_cookie(SESSION_COOKIE)
    return response

# ==========================================================
# Dependencies used by the protected routes
# ==========================================================

def get_current_company(request : Request,db : Session = Depends(get_db)):
    session = read_session(request)
    if not session or session["role"] != ROLE_COMPANY:
        raise HTTPException(
            status_code=401,
            detail="Please log in with a company account"
        )
    company = db.query(Company).filter(Company.id == session["user_id"]).first()
    if not company:
        raise HTTPException(
            status_code=401,
            detail="Please log in with a company account"
        )
    return company

def get_current_job_seeker(request : Request,db : Session = Depends(get_db)):
    session = read_session(request)
    if not session or session["role"] != ROLE_JOB_SEEKER:
        raise HTTPException(
            status_code=401,
            detail="Please log in with a job seeker account"
        )
    job_seeker = db.query(JobSeeker).filter(JobSeeker.id == session["user_id"]).first()
    if not job_seeker or not job_seeker.is_active:
        raise HTTPException(
            status_code=401,
            detail="Please log in with a job seeker account"
        )
    return job_seeker
