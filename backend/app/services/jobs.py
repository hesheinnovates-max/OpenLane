from app.models.job import Job
from app.models.business import Business
from app.models.companies import Company

# ==========================================================
# Shared helpers for turning jobs into JSON
# ==========================================================

def to_iso(value):
    return value.isoformat() if value else None

def job_query(db):
    # Job + the business it belongs to + the company that owns the business
    return (db.query(Job,Business,Company)
        .join(Business,Job.business_id == Business.id)
        .join(Company,Business.company_id == Company.id))

def job_to_dict(job,business,company,applications_count=None,include_contact=True):
    data = {
        "id": job.id,
        "title": job.name,
        "description": job.description,
        "requirements": job.requirements or "",
        "job_type": job.job_type or "",
        "location": job.location or "",
        "status": job.status,
        "created_at": to_iso(job.created_at),
        "updated_at": to_iso(job.updated_at),
        "business": {"id": business.id,"name": business.name},
        "company": {
            "id": company.id,
            "name": company.company_name,
            "description": company.description or "",
        },
    }
    if include_contact:
        data["company"]["email"] = company.email
        data["company"]["phone"] = company.phone or ""
        data["company"]["alt_phone"] = company.alt_phone or ""
    if applications_count is not None:
        data["applications_count"] = applications_count
    return data
