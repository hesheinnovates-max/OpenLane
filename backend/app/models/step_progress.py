from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey , UniqueConstraint

from app.db.base import Base

# Tracks which steps a job seeker has completed for a selected skill
class StepProgress(Base):
    __tablename__ = "step_progresses"
    __table_args__ = (UniqueConstraint("job_seeker_skill_id","step_id",name="uq_step_progress_skill_step"),)
    id = Column(Integer,primary_key=True)
    job_seeker_skill_id = Column(Integer,ForeignKey("job_seeker_skills.id",ondelete="CASCADE"),nullable=False)
    step_id = Column(Integer,ForeignKey("skill_steps.id",ondelete="CASCADE"),nullable=False)
    completed = Column(Boolean,nullable=False,default=False)
    completed_at = Column(DateTime(timezone=True),nullable=True)
