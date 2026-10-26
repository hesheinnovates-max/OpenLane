from sqlalchemy import func

from app.models.skill import Skill
from app.models.skill_step import SkillStep
from app.models.job_seeker_skill import JobSeekerSkill
from app.models.step_progress import StepProgress
from app.services.progress import skill_percentage , display_percentage , skill_status , overall_percentage
from app.services.jobs import to_iso

# ==========================================================
# Builds a job seeker's skills with their progress.
# Percentages are always calculated here on the backend
# from the steps , never trusted from the browser.
# ==========================================================

def skill_steps(db,skill_id):
    return (db.query(SkillStep)
        .filter(SkillStep.skill_id == skill_id)
        .order_by(SkillStep.order_index,SkillStep.id)
        .all())

def calculate(db,selected,steps=None):
    # Returns (completed_required , total_required , completed_step_ids)
    if steps is None:
        steps = skill_steps(db,selected.skill_id)
    required_ids = {step.id for step in steps if step.required}
    done_ids = {row.step_id for row in db.query(StepProgress).filter(
        StepProgress.job_seeker_skill_id == selected.id,
        StepProgress.completed == True).all()}
    return len(required_ids & done_ids) , len(required_ids) , done_ids

def selected_skill_to_dict(db,selected,skill,include_steps=True):
    steps = skill_steps(db,skill.id)
    completed , total , done_ids = calculate(db,selected,steps)
    percentage = skill_percentage(completed,total)
    data = {
        "id": selected.id,
        "skill_id": skill.id,
        "name": skill.name,
        "description": skill.description or "",
        "category": skill.category or "",
        "status": selected.status,
        "percentage": percentage,
        "display_percentage": display_percentage(percentage),
        "completed_steps": completed,
        "total_steps": total,
        "configured": total > 0,
        "started_at": to_iso(selected.started_at),
        "completed_at": to_iso(selected.completed_at),
    }
    if include_steps:
        data["steps"] = [{
            "id": step.id,
            "title": step.title,
            "description": step.description or "",
            "required": step.required,
            "completed": step.id in done_ids,
        } for step in steps]
    return data

def learner_summary(db,job_seeker_id,include_steps=True):
    rows = (db.query(JobSeekerSkill,Skill)
        .join(Skill,JobSeekerSkill.skill_id == Skill.id)
        .filter(JobSeekerSkill.job_seeker_id == job_seeker_id)
        .order_by(JobSeekerSkill.created_at,JobSeekerSkill.id)
        .all())
    skills = [selected_skill_to_dict(db,selected,skill,include_steps) for selected , skill in rows]
    overall = overall_percentage([item["percentage"] for item in skills])
    counts = {"Not Started":0,"In Progress":0,"Completed":0}
    for item in skills:
        counts[item["status"]] = counts.get(item["status"],0) + 1
    return {
        "skills": skills,
        "overall": {
            "percentage": overall,
            "display_percentage": display_percentage(overall),
            "counts": counts,
            "total": len(skills),
            "formula": "Average of the completion percentages of your selected skills",
        },
    }

def refresh_status(db,selected):
    # Keep the stored status in line with the steps (spec 7.1)
    completed , total , _ = calculate(db,selected)
    status = skill_status(completed,total,selected.started_at is not None)
    if status != "Not Started" and selected.started_at is None:
        selected.started_at = func.now()
    if status == "Completed" and selected.completed_at is None:
        selected.completed_at = func.now()
    if status != "Completed":
        selected.completed_at = None
    selected.status = status
    return status
