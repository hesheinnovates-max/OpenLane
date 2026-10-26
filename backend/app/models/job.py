from sqlalchemy import Column , Text , Integer , Boolean , DateTime
from sqlalchemy import ForeignKey , func , String

from app.db.base import Base

# Allowed values for the job status
JOB_STATUSES = ["draft","published","closed"]
JOB_TYPES = ["Full-time","Part-time","Contract","Internship","Learnership","Temporary","Volunteer"]

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer,primary_key=True)
    name = Column(String(255),nullable=False)
    description = Column(Text,nullable=False)
    requirements = Column(Text,nullable=True)
    job_type = Column(String(50),nullable=True)
    location = Column(String(255),nullable=True)
    status = Column(String(20),nullable=False,default="draft",server_default="draft")
    business_id = Column(Integer,ForeignKey("businesses.id"),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=True,onupdate=func.now())
