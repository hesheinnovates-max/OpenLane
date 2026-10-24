from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey

from app.db.base import Base

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer,nullable=False,primary_key=True)
    name = Column(String(255),nullable=False)
    description = Column(Text,nullable=True)
    email = Column(String(255),nullable=False,unique = True)
    phone = Column(String(20),nullable=True)
    password_hash = Column(String(255),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)