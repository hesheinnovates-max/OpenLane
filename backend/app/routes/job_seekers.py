from pathlib import Path
from fastapi import APIRouter , Form , Depends , HTTPException , Request
from fastapi.responses import HTMLResponse , RedirectResponse

from app.db.dependencies import get_db
from app.models.job_seeker import JobSeeker
from app.models.job_seeker_profile import JobSeekerProfile
from app.models.skill import Skill
from app.models.skill_step import SkillStep
from app.models.job_seeker_skill import JobSeekerSkill
from app.models.step_progress import StepProgress
from app.models.applications import Application
from app.models.job import Job
from app.routes.validations import validate_the_email , validate_phone , normalize_phone , validate_required , validate_optional_url
from app.routes.sign_in import phone_variants
from app.services.auth import get_current_job_seeker , read_session , ROLE_JOB_SEEKER
from app.services.learner import learner_summary , selected_skill_to_dict , skill_steps , refresh_status
from app.services.jobs import job_query , job_to_dict , to_iso

from sqlalchemy import func , or_
from sqlalchemy.orm import Session

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

PAGE = PROJECT_ROOT/"frontend"/'templates'

@router.get("/job-seeker/dashboard",response_class=HTMLResponse)
def job_seeker_dashboard(request : Request):
    session = read_session(request)
    if not session or session["role"] != ROLE_JOB_SEEKER:
        return RedirectResponse("/job-seeker/login",status_code=303)
    return (PAGE/"job-seeker-dashboard.html").read_text(encoding="utf-8")


# ===========================================================
# ------------ Helpers --------------------------------------
# ===========================================================

def get_selected_skill(db,job_seeker,selected_id):
    # A job seeker can only change their own progress
    row = (db.query(JobSeekerSkill,Skill)
        .join(Skill,JobSeekerSkill.skill_id == Skill.id)
        .filter(JobSeekerSkill.id == selected_id,JobSeekerSkill.job_seeker_id == job_seeker.id)
        .first())
    if not row:
        raise HTTPException(
            status_code=404,
            detail="This skill is not in your learning list"
        )
    return row

def skill_to_dict(db,skill,selected_ids=None):
    steps = skill_steps(db,skill.id)
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description or "",
        "category": skill.category or "",
        "steps_count": len([step for step in steps if step.required]),
        "steps": [{"id": step.id,"title": step.title,"description": step.description or ""} for step in steps],
        "selected": skill.id in (selected_ids or set()),
    }

def progress_response(db,job_seeker,selected,skill,message):
    return {
        "message": message,
        "skill": selected_skill_to_dict(db,selected,skill),
        "overall": learner_summary(db,job_seeker.id,include_steps=False)["overall"],
    }


# ===========================================================
# ------------ Skill Catalogue ------------------------------
# ===========================================================

@router.get("/api/skills")
def skill_catalogue(request : Request,search : str = "",category : str = "",db : Session = Depends(get_db)):
    query = db.query(Skill).filter(Skill.is_active == True)
    if search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(Skill.name.ilike(pattern),Skill.description.ilike(pattern),Skill.category.ilike(pattern)))
    if category.strip():
        query = query.filter(Skill.category == category.strip())

    selected_ids = set()
    session = read_session(request)
    if session and session["role"] == ROLE_JOB_SEEKER:
        selected_ids = {row.skill_id for row in db.query(JobSeekerSkill).filter(JobSeekerSkill.job_seeker_id == session["user_id"]).all()}

    return [skill_to_dict(db,skill,selected_ids) for skill in query.order_by(Skill.category,Skill.name).all()]

@router.get("/api/skills/{skill_id}")
def skill_detail(skill_id : int,db : Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.id == skill_id,Skill.is_active == True).first()
    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )
    return skill_to_dict(db,skill)


# ===========================================================
# ------------ Job Seeker Functionality ---------------------
# ===========================================================

@router.get("/api/job-seeker/skills")
def my_skills(job_seeker : JobSeeker = Depends(get_current_job_seeker),db : Session = Depends(get_db)):
    return learner_summary(db,job_seeker.id)

@router.post("/api/job-seeker/skills")
def add_skill(skill_id : int = Form(...),
    job_seeker : JobSeeker = Depends(get_current_job_seeker),
    db : Session = Depends(get_db)):

    skill = db.query(Skill).filter(Skill.id == skill_id,Skill.is_active == True).first()
    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    exists = db.query(JobSeekerSkill).filter(JobSeekerSkill.job_seeker_id == job_seeker.id,JobSeekerSkill.skill_id == skill.id).first()
    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"{skill.name} is already in your learning list"
        )

    selected = JobSeekerSkill(
        job_seeker_id=job_seeker.id,
        skill_id=skill.id,
        proficiency_level="Beginner",
        status="Not Started",
    )
    db.add(selected)
    try:
        db.commit()
        db.refresh(selected)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{skill.name} is already in your learning list"
        )

    return progress_response(db,job_seeker,selected,skill,f"{skill.name} added to your learning list")

@router.post("/api/job-seeker/skills/{selected_id}/start")
def start_skill(selected_id : int,job_seeker : JobSeeker = Depends(get_current_job_seeker),db : Session = Depends(get_db)):
    selected , skill = get_selected_skill(db,job_seeker,selected_id)
    if selected.started_at is None:
        selected.started_at = func.now()
    refresh_status(db,selected)
    db.commit()
    db.refresh(selected)
    return progress_response(db,job_seeker,selected,skill,f"You started {skill.name}")

@router.patch("/api/job-seeker/skills/{selected_id}/steps/{step_id}")
def update_step(selected_id : int,step_id : int,
    completed : bool = Form(...),
    job_seeker : JobSeeker = Depends(get_current_job_seeker),
    db : Session = Depends(get_db)):

    selected , skill = get_selected_skill(db,job_seeker,selected_id)

    step = db.query(SkillStep).filter(SkillStep.id == step_id,SkillStep.skill_id == skill.id).first()
    if not step:
        raise HTTPException(
            status_code=404,
            detail="This step does not belong to the skill"
        )

    progress = db.query(StepProgress).filter(StepProgress.job_seeker_skill_id == selected.id,StepProgress.step_id == step.id).first()
    if not progress:
        progress = StepProgress(job_seeker_skill_id=selected.id,step_id=step.id,completed=False)
        db.add(progress)

    progress.completed = completed
    progress.completed_at = func.now() if completed else None
    db.flush()

    status = refresh_status(db,selected)
    try:
        db.commit()
        db.refresh(selected)
    except Exception:
        db.rollback()
        raise

    if status == "Completed":
        message = f"Well done! You completed {skill.name}"
    elif completed:
        message = "Step marked as complete"
    else:
        message = "Step marked as not complete"
    return progress_response(db,job_seeker,selected,skill,message)

@router.delete("/api/job-seeker/skills/{selected_id}")
def remove_skill(selected_id : int,job_seeker : JobSeeker = Depends(get_current_job_seeker),db : Session = Depends(get_db)):
    selected , skill = get_selected_skill(db,job_seeker,selected_id)
    db.query(StepProgress).filter(StepProgress.job_seeker_skill_id == selected.id).delete()
    db.delete(selected)
    db.commit()
    return {"message":f"{skill.name} removed from your learning list"}


# ===========================================================
# ------------ Applications ---------------------------------
# ===========================================================

@router.get("/api/job-seeker/applications")
def my_applications(job_seeker : JobSeeker = Depends(get_current_job_seeker),db : Session = Depends(get_db)):
    rows = (job_query(db).add_entity(Application)
        .join(Application,Application.job_id == Job.id)
        .filter(Application.job_seeker_id == job_seeker.id)
        .order_by(Application.created_at.desc(),Application.id.desc())
        .all())
    return [{
        "id": application.id,
        "status": application.status,
        "message": application.message or "",
        "created_at": to_iso(application.created_at),
        "updated_at": to_iso(application.updated_at),
        "job": job_to_dict(job,business,company),
    } for job , business , company , application in rows]

@router.delete("/api/job-seeker/applications/{application_id}")
def withdraw_application(application_id : int,job_seeker : JobSeeker = Depends(get_current_job_seeker),db : Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id,Application.job_seeker_id == job_seeker.id).first()
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )
    if application.status not in ["pending","reviewed"]:
        raise HTTPException(
            status_code=409,
            detail="This application has already been decided and cannot be withdrawn"
        )
    db.delete(application)
    db.commit()
    return {"message":"Application withdrawn"}


# ===========================================================
# ------------ Profile --------------------------------------
# ===========================================================

def profile_to_dict(job_seeker,profile):
    return {
        "full_name": job_seeker.full_name,
        "email": job_seeker.email or "",
        "phone": job_seeker.phone or "",
        "location": profile.location if profile else "",
        "bio": (profile.bio or "") if profile else "",
        "portfolio_url": (profile.portfolio_url or "") if profile else "",
        "created_at": to_iso(job_seeker.created_at),
    }

@router.get("/api/job-seeker/profile")
def my_profile(job_seeker : JobSeeker = Depends(get_current_job_seeker),db : Session = Depends(get_db)):
    profile = db.query(JobSeekerProfile).filter(JobSeekerProfile.job_seeker_id == job_seeker.id).first()
    return profile_to_dict(job_seeker,profile)

@router.put("/api/job-seeker/profile")
def update_profile(full_name : str = Form(...),
    email : str = Form(""),
    phone : str = Form(""),
    location : str = Form(""),
    bio : str = Form(""),
    portfolio_url : str = Form(""),
    job_seeker : JobSeeker = Depends(get_current_job_seeker),
    db : Session = Depends(get_db)):

    full_name = full_name.strip()
    email = email.strip().lower()
    phone = normalize_phone(phone)
    location = location.strip()
    bio = bio.strip()
    portfolio_url = portfolio_url.strip()

    if not email and not phone:
        raise HTTPException(
        status_code=409,
        detail= "Email or Phone required")

    true_table = [validate_required(full_name,"Full name",150),validate_optional_url(portfolio_url)]
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

    if email and db.query(JobSeeker).filter(func.lower(JobSeeker.email) == email,JobSeeker.id != job_seeker.id).first():
        raise HTTPException(
            status_code=409,
            detail="Another account already uses this email"
        )
    if phone and db.query(JobSeeker).filter(JobSeeker.phone.in_(phone_variants(phone)),JobSeeker.id != job_seeker.id).first():
        raise HTTPException(
            status_code=409,
            detail="Another account already uses this phone number"
        )

    job_seeker.full_name = full_name
    job_seeker.email = email or None
    job_seeker.phone = phone or None

    profile = db.query(JobSeekerProfile).filter(JobSeekerProfile.job_seeker_id == job_seeker.id).first()
    if not profile:
        profile = JobSeekerProfile(job_seeker_id=job_seeker.id,location="")
        db.add(profile)
    profile.location = location
    profile.bio = bio or None
    profile.portfolio_url = portfolio_url or None
    profile.updated_at = func.now()

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return {"message":"Profile saved","profile":profile_to_dict(job_seeker,profile)}
