from sqlalchemy import ForeignKey , func , Integer , Boolean , Text , String , Column , DateTime , UniqueConstraint
from app.db.base import Base

# Allowed values for the application status
APPLICATION_STATUSES = ["pending","reviewed","shortlisted","rejected","accepted"]

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_seeker_id","job_id",name="uq_application_job_seeker_job"),)
    id = Column(Integer,primary_key = True)
    job_seeker_id = Column(Integer,ForeignKey("job_seekers.id"),nullable=False)
    job_id = Column(Integer,ForeignKey("jobs.id"),nullable=False)
    message = Column(Text,nullable=True)
    status = Column(String(20),nullable=False,default="pending")
    created_at = Column(DateTime(timezone=True), server_default = func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default = func.now(),nullable=False,onupdate=func.now())
