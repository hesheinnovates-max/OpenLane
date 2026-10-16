from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey

from app.db.base import Base

class JobSeekerSkill(Base):
    __tablename__ = "job_seeker_skills"
    id  = Column(Integer,primary_key=True)
    job_seeker_id = Column(Integer,ForeignKey("job_seekers.id"),nullable=False)
    skill_id = Column(Integer,ForeignKey("skills.id"),nullable=False)
    proficiency_level = Column(String(30),nullable=False)
    status = Column(String(30),nullable=False,default="Selected")
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True),server_onupdate=func.now(),nullable=True)