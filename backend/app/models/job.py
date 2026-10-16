from sqlalchemy import Column , Text , Integer , Boolean , DateTime
from sqlalchemy import ForeignKey , func , String

from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer,primary_key=True)
    name = Column(String(255),nullable=False)
    description = Column(Text,nullable=False)
    business_id = Column(Integer,ForeignKey("businesses.id"),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
