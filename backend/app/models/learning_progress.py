from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey

from app.db.base import Base


class LearningProgress(Base):
    __tablename__ = "learning_progresses"
    id = Column(Integer,primary_key=True)
    job_seeker_id = Column(Integer,ForeignKey("job_seekers.id"),nullable=False)
    course_id = Column(Integer,ForeignKey("courses.id"),nullable=False)
    progress_percentage = Column(Integer,nullable=False,default=0)
    status = Column(String(20),nullable=False,default="Not started")
    started_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True),server_onupdate=func.now(),nullable=False)
    completed_at = Column(DateTime(timezone=True),server_onupdate=func.now(),nullable=True)

