from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey

from app.db.base import Base

class JobSeekerProfile(Base):
    __tablename__ = "job_seeker_profiles"
    id = Column(Integer,primary_key=True)
    job_seeker_id = Column(Integer,ForeignKey("job_seekers.id"),nullable=False)
    location = Column(String(255),nullable=False)
    bio = Column(Text,nullable=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True),server_onupdate=func.now(),nullable=True)
