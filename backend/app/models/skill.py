from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey

from app.db.base import Base

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer,primary_key=True)
    name = Column(String(100),nullable=True,unique=True)
    description = Column(Text,nullable=True)
    category = Column(String(100),nullable=True)
    is_active = Column(Boolean,nullable=False,default=True,server_default="true")
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
