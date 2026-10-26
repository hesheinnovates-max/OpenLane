from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey

from app.db.base import Base

# The milestones used to define when a skill is complete
class SkillStep(Base):
    __tablename__ = "skill_steps"
    id = Column(Integer,primary_key=True)
    skill_id = Column(Integer,ForeignKey("skills.id"),nullable=False)
    title = Column(String(255),nullable=False)
    description = Column(Text,nullable=True)
    order_index = Column(Integer,nullable=False,default=0)
    required = Column(Boolean,nullable=False,default=True,server_default="true")
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
