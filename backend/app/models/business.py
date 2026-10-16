from sqlalchemy import ForeignKey , func , Integer , Boolean , Text , String , Column , DateTime
from app.db.base import Base

class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer,primary_key=True)
    company_id = Column(Integer,ForeignKey("companies.id"),nullable=False)
    name = Column(String(255),nullable=False)
    description = Column(Text,nullable=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
