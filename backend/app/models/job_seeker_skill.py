from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey , UniqueConstraint

from app.db.base import Base

# Allowed values for a selected skill
SKILL_STATUSES = ["Not Started","In Progress","Completed"]

class JobSeekerSkill(Base):
    __tablename__ = "job_seeker_skills"
    __table_args__ = (UniqueConstraint("job_seeker_id","skill_id",name="uq_job_seeker_skill"),)
    id  = Column(Integer,primary_key=True)
    job_seeker_id = Column(Integer,ForeignKey("job_seekers.id"),nullable=False)
    skill_id = Column(Integer,ForeignKey("skills.id"),nullable=False)
    proficiency_level = Column(String(30),nullable=False,default="Beginner")
    status = Column(String(30),nullable=False,default="Not Started")
    started_at = Column(DateTime(timezone=True),nullable=True)
    completed_at = Column(DateTime(timezone=True),nullable=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True),server_onupdate=func.now(),nullable=True)
