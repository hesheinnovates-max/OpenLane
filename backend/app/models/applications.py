from sqlalchemy import ForeignKey , func , Integer , Boolean , Text , String , Column , DateTime
from app.db.base import Base


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer,primary_key = True)
    job_seeker_id = Column(Integer,ForeignKey("job_seekers.id"),nullable=False)
    job_id = Column(Integer,ForeignKey("jobs.id"),nullable=False)
    status = Column(String(20),nullable=False,default="pending")
    created_at = Column(DateTime(timezone=True), server_default = func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default = func.now(),nullable=False,onupdate=func.now())