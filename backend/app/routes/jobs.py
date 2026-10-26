from pathlib import Path
from fastapi import APIRouter , Form , Depends , HTTPException , Request
from fastapi.responses import HTMLResponse

from app.db.dependencies import get_db
from app.models.job import Job , JOB_TYPES
from app.models.business import Business
from app.models.companies import Company
from app.models.applications import Application
from app.models.job_seeker import JobSeeker
from app.services.auth import get_current_job_seeker , read_session , ROLE_JOB_SEEKER
from app.services.jobs import job_query , job_to_dict

from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

PAGE = PROJECT_ROOT/"frontend"/'templates'

# ==========================================================
# Public job listings (spec 5.5 and 6.3).
# Only published jobs are shown , drafts and closed jobs are hidden.
# ==========================================================

@router.get("/jobs",response_class=HTMLResponse)
def jobs_page():
    return (PAGE/"jobs.html").read_text(encoding="utf-8")

def applied_job_ids(request,db):
    session = read_session(request)
    if session and session["role"] == ROLE_JOB_SEEKER:
        return {row.job_id for row in db.query(Application).filter(Application.job_seeker_id == session["user_id"]).all()}
    return set()

@router.get("/api/jobs")
def published_jobs(request : Request,search : str = "",job_type : str = "",location : str = "",db : Session = Depends(get_db)):
    query = job_query(db).filter(Job.status == "published")
    if search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(
            Job.name.ilike(pattern),
            Job.description.ilike(pattern),
            Job.requirements.ilike(pattern),
            Company.company_name.ilike(pattern),
        ))
    if job_type.strip():
        query = query.filter(Job.job_type == job_type.strip())
    if location.strip():
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    applied = applied_job_ids(request,db)
    result = []
    for job , business , company in query.order_by(Job.created_at.desc(),Job.id.desc()).all():
        data = job_to_dict(job,business,company)
        data["applied"] = job.id in applied
        result.append(data)
    return {"jobs":result,"job_types":JOB_TYPES}

@router.get("/api/jobs/{job_id}")
def published_job(job_id : int,request : Request,db : Session = Depends(get_db)):
    row = job_query(db).filter(Job.id == job_id,Job.status == "published").first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail="This job is not available"
        )
    job , business , company = row
    data = job_to_dict(job,business,company)
    data["applied"] = job.id in applied_job_ids(request,db)
    return data

@router.post("/api/jobs/{job_id}/apply")
def apply_for_job(job_id : int,
    message : str = Form(""),
    job_seeker : JobSeeker = Depends(get_current_job_seeker),
    db : Session = Depends(get_db)):

    job = db.query(Job).filter(Job.id == job_id,Job.status == "published").first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail="This job is not available"
        )

    exists = db.query(Application).filter(Application.job_id == job.id,Application.job_seeker_id == job_seeker.id).first()
    if exists:
        raise HTTPException(
            status_code=409,
            detail="You already applied for this job"
        )

    message = message.strip()
    if len(message) > 2000:
        raise HTTPException(
            status_code=409,
            detail="Your message must be 2000 characters or less"
        )

    application = Application(
        job_seeker_id=job_seeker.id,
        job_id=job.id,
        message=message or None,
        status="pending",
    )
    db.add(application)
    try:
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="You already applied for this job"
        )

    return {"message":"Application sent. You can follow it under My applications.","application_id":application.id}
