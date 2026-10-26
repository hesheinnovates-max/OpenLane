from pathlib import Path
from fastapi import APIRouter , Form , Depends , HTTPException , Request
from fastapi.responses import HTMLResponse , RedirectResponse

from app.db.dependencies import get_db
from app.models.companies import Company
from app.models.business import Business
from app.models.job import Job , JOB_STATUSES , JOB_TYPES
from app.models.applications import Application , APPLICATION_STATUSES
from app.models.job_seeker import JobSeeker
from app.models.job_seeker_profile import JobSeekerProfile
from app.routes.validations import validate_the_email , validate_phone , normalize_phone , validate_required
from app.services.auth import get_current_company , read_session , ROLE_COMPANY
from app.services.jobs import job_query , job_to_dict , to_iso
from app.services.learner import learner_summary

from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

PAGE = PROJECT_ROOT/"frontend"/'templates'


# ==========================================================
# Helpers
# ==========================================================

def check(true_table):
    # Same validation pattern used in register.py
    for n in range(len(true_table)):
        if true_table[n] != [True]:
            raise HTTPException(
            status_code=409,
            detail=true_table[n][1]
            )

def get_company_job(db,company,job_id):
    # A company can only see / change its own jobs , changing the id in the URL is not enough
    row = job_query(db).filter(Job.id == job_id,Company.id == company.id).first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    return row

def get_company_business(db,company,business_id):
    business = db.query(Business).filter(Business.id == business_id,Business.company_id == company.id).first()
    if not business:
        raise HTTPException(
            status_code=404,
            detail="Business not found"
        )
    return business

def default_business(db,company):
    # Use the first business , create one with the company name if there is none
    business = db.query(Business).filter(Business.company_id == company.id).order_by(Business.id).first()
    if not business:
        business = Business(company_id=company.id,name=company.company_name,description="Main business")
        db.add(business)
        db.flush()
    return business

def applications_count(db,job_id):
    return db.query(Application).filter(Application.job_id == job_id).count()

def validate_job_fields(title,description,requirements,job_type,location,status):
    check([
        validate_required(title,"Job title",255),
        validate_required(description,"Work description"),
        validate_required(requirements,"Requirements"),
    ])
    if job_type and job_type not in JOB_TYPES:
        raise HTTPException(
            status_code=409,
            detail="Choose a valid job type"
        )
    if location and len(location) > 255:
        raise HTTPException(
            status_code=409,
            detail="Location must be 255 characters or less"
        )
    if status not in JOB_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Status must be draft, published or closed"
        )

def business_to_dict(db,business):
    return {
        "id": business.id,
        "name": business.name,
        "description": business.description or "",
        "jobs_count": db.query(Job).filter(Job.business_id == business.id).count(),
    }

def company_to_dict(company):
    return {
        "id": company.id,
        "company_name": company.company_name,
        "email": company.email,
        "phone": company.phone or "",
        "alt_phone": company.alt_phone or "",
        "description": company.description or "",
        "created_at": to_iso(company.created_at),
    }

# ==========================================================
# All get methods for the companies
# ==========================================================

@router.get("/company/dashboard",response_class=HTMLResponse)
def company_dashboard(request : Request):
    session = read_session(request)
    if not session or session["role"] != ROLE_COMPANY:
        return RedirectResponse("/company/login",status_code=303)
    return (PAGE/"company-dashboard.html").read_text(encoding="utf-8")

@router.get("/api/company/overview")
def company_overview(company : Company = Depends(get_current_company),db : Session = Depends(get_db)):
    jobs = job_query(db).filter(Company.id == company.id).all()
    job_ids = [job.id for job , _ , _ in jobs]
    stats = {
        "jobs": len(jobs),
        "published": len([1 for job , _ , _ in jobs if job.status == "published"]),
        "draft": len([1 for job , _ , _ in jobs if job.status == "draft"]),
        "closed": len([1 for job , _ , _ in jobs if job.status == "closed"]),
        "applications": 0,
        "pending": 0,
    }
    if job_ids:
        stats["applications"] = db.query(Application).filter(Application.job_id.in_(job_ids)).count()
        stats["pending"] = db.query(Application).filter(Application.job_id.in_(job_ids),Application.status == "pending").count()
    businesses = db.query(Business).filter(Business.company_id == company.id).order_by(Business.id).all()
    return {
        "company": company_to_dict(company),
        "stats": stats,
        "businesses": [business_to_dict(db,business) for business in businesses],
        "job_types": JOB_TYPES,
        "job_statuses": JOB_STATUSES,
        "application_statuses": APPLICATION_STATUSES,
    }

@router.get("/api/company/jobs")
def company_jobs(company : Company = Depends(get_current_company),db : Session = Depends(get_db)):
    rows = job_query(db).filter(Company.id == company.id).order_by(Job.created_at.desc(),Job.id.desc()).all()
    return [job_to_dict(job,business,owner,applications_count(db,job.id)) for job , business , owner in rows]

@router.get("/api/company/jobs/{job_id}")
def company_job(job_id : int,company : Company = Depends(get_current_company),db : Session = Depends(get_db)):
    job , business , owner = get_company_job(db,company,job_id)
    return job_to_dict(job,business,owner,applications_count(db,job.id))

@router.get("/api/company/applications")
def company_applications(job_id : int = None,status : str = None,
    company : Company = Depends(get_current_company),db : Session = Depends(get_db)):

    query = (db.query(Application,Job,JobSeeker)
        .join(Job,Application.job_id == Job.id)
        .join(Business,Job.business_id == Business.id)
        .join(JobSeeker,Application.job_seeker_id == JobSeeker.id)
        .filter(Business.company_id == company.id))
    if job_id:
        query = query.filter(Job.id == job_id)
    if status:
        query = query.filter(Application.status == status)

    result = []
    for application , job , seeker in query.order_by(Application.created_at.desc(),Application.id.desc()).all():
        profile = db.query(JobSeekerProfile).filter(JobSeekerProfile.job_seeker_id == seeker.id).first()
        summary = learner_summary(db,seeker.id,include_steps=False)
        result.append({
            "id": application.id,
            "status": application.status,
            "message": application.message or "",
            "created_at": to_iso(application.created_at),
            "updated_at": to_iso(application.updated_at),
            "job": {"id": job.id,"title": job.name,"status": job.status},
            "applicant": {
                "id": seeker.id,
                "full_name": seeker.full_name,
                "email": seeker.email or "",
                "phone": seeker.phone or "",
                "location": profile.location if profile else "",
                "bio": (profile.bio or "") if profile else "",
                "portfolio_url": (profile.portfolio_url or "") if profile else "",
                "skills": [{
                    "name": item["name"],
                    "status": item["status"],
                    "display_percentage": item["display_percentage"],
                } for item in summary["skills"]],
                "overall": summary["overall"]["display_percentage"],
            },
        })
    return result

# =========================================================
# POST / PUT / PATCH / DELETE METHODS
# =========================================================

@router.put("/api/company/profile")
def update_company_profile(company_name : str = Form(...),
    email : str = Form(...),
    phone : str = Form(...),
    alt_phone : str = Form(""),
    description : str = Form(""),
    company : Company = Depends(get_current_company),
    db : Session = Depends(get_db)):

    company_name = company_name.strip()
    email = email.strip().lower()
    phone = normalize_phone(phone)
    alt_phone = normalize_phone(alt_phone)
    description = description.strip()

    true_table = [validate_required(company_name,"Company name",255),validate_the_email(email),validate_phone(phone)]
    if alt_phone:
        true_table.append(validate_phone(alt_phone))
    check(true_table)

    taken = db.query(Company).filter(func.lower(Company.email) == email,Company.id != company.id).first()
    if taken:
        raise HTTPException(
            status_code=409,
            detail="Another company already uses this email"
        )

    company.company_name = company_name
    company.email = email
    company.phone = phone
    company.alt_phone = alt_phone or None
    company.description = description or None

    try:
        db.commit()
        db.refresh(company)
    except Exception:
        db.rollback()
        raise

    return {"message":"Company details saved","company":company_to_dict(company)}

@router.post("/api/company/businesses")
def add_business(name : str = Form(...),
    description : str = Form(""),
    company : Company = Depends(get_current_company),
    db : Session = Depends(get_db)):

    name = name.strip()
    check([validate_required(name,"Business name",255)])

    business = Business(company_id=company.id,name=name,description=description.strip() or None)
    db.add(business)
    try:
        db.commit()
        db.refresh(business)
    except Exception:
        db.rollback()
        raise
    return {"message":"Business added","business":business_to_dict(db,business)}

@router.put("/api/company/businesses/{business_id}")
def update_business(business_id : int,
    name : str = Form(...),
    description : str = Form(""),
    company : Company = Depends(get_current_company),
    db : Session = Depends(get_db)):

    business = get_company_business(db,company,business_id)
    name = name.strip()
    check([validate_required(name,"Business name",255)])
    business.name = name
    business.description = description.strip() or None
    db.commit()
    return {"message":"Business saved","business":business_to_dict(db,business)}

@router.delete("/api/company/businesses/{business_id}")
def delete_business(business_id : int,company : Company = Depends(get_current_company),db : Session = Depends(get_db)):
    business = get_company_business(db,company,business_id)
    if db.query(Job).filter(Job.business_id == business.id).count() > 0:
        raise HTTPException(
            status_code=409,
            detail="This business still has jobs. Move or delete them first."
        )
    db.delete(business)
    db.commit()
    return {"message":"Business removed"}

@router.post("/api/company/jobs")
def add_job(title : str = Form(...),
    description : str = Form(...),
    requirements : str = Form(...),
    job_type : str = Form(""),
    location : str = Form(""),
    status : str = Form("draft"),
    business_id : str = Form(""),
    company : Company = Depends(get_current_company),
    db : Session = Depends(get_db)):

    title = title.strip()
    description = description.strip()
    requirements = requirements.strip()
    job_type = job_type.strip()
    location = location.strip()
    status = status.strip().lower()

    validate_job_fields(title,description,requirements,job_type,location,status)

    if business_id.strip().isdigit():
        business = get_company_business(db,company,int(business_id))
    else:
        business = default_business(db,company)

    new_job = Job(
        name=title,
        description=description,
        requirements=requirements,
        job_type=job_type or None,
        location=location or None,
        status=status,
        business_id=business.id,
    )
    db.add(new_job)

    try:
        db.commit()
        db.refresh(new_job)
    except Exception:
        db.rollback()
        raise

    message = "Job published, job seekers can now see it" if status == "published" else "Job saved as a draft"
    return {"message":message,"job":job_to_dict(new_job,business,company,0)}

@router.put("/api/company/jobs/{job_id}")
def update_job(job_id : int,
    title : str = Form(...),
    description : str = Form(...),
    requirements : str = Form(...),
    job_type : str = Form(""),
    location : str = Form(""),
    status : str = Form(None),
    business_id : str = Form(""),
    company : Company = Depends(get_current_company),
    db : Session = Depends(get_db)):

    job , business , owner = get_company_job(db,company,job_id)

    title = title.strip()
    description = description.strip()
    requirements = requirements.strip()
    job_type = job_type.strip()
    location = location.strip()
    status = (status or job.status).strip().lower()

    validate_job_fields(title,description,requirements,job_type,location,status)

    if business_id.strip().isdigit() and int(business_id) != business.id:
        business = get_company_business(db,company,int(business_id))

    job.name = title
    job.description = description
    job.requirements = requirements
    job.job_type = job_type or None
    job.location = location or None
    job.status = status
    job.business_id = business.id

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return {"message":"Job saved","job":job_to_dict(job,business,owner,applications_count(db,job.id))}

@router.patch("/api/company/jobs/{job_id}/status")
def change_job_status(job_id : int,
    status : str = Form(...),
    company : Company = Depends(get_current_company),
    db : Session = Depends(get_db)):

    job , business , owner = get_company_job(db,company,job_id)
    status = status.strip().lower()
    if status not in JOB_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Status must be draft, published or closed"
        )
    job.status = status
    db.commit()
    db.refresh(job)

    messages = {
        "published": "Job published, job seekers can now see it",
        "draft": "Job unpublished and moved to drafts",
        "closed": "Job closed, it is no longer visible to job seekers",
    }
    return {"message":messages[status],"job":job_to_dict(job,business,owner,applications_count(db,job.id))}

@router.delete("/api/company/jobs/{job_id}")
def delete_job(job_id : int,company : Company = Depends(get_current_company),db : Session = Depends(get_db)):
    job , business , owner = get_company_job(db,company,job_id)
    if applications_count(db,job.id) > 0:
        raise HTTPException(
            status_code=409,
            detail="This job has applications. Close it instead of deleting it."
        )
    db.delete(job)
    db.commit()
    return {"message":"Job deleted"}

@router.patch("/api/company/applications/{application_id}/status")
def change_application_status(application_id : int,
    status : str = Form(...),
    company : Company = Depends(get_current_company),
    db : Session = Depends(get_db)):

    status = status.strip().lower()
    if status not in APPLICATION_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Choose a valid application status"
        )

    application = (db.query(Application)
        .join(Job,Application.job_id == Job.id)
        .join(Business,Job.business_id == Business.id)
        .filter(Application.id == application_id,Business.company_id == company.id)
        .first())
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    application.status = status
    db.commit()
    return {"message":f"Application marked as {status}","status":status}
