from sqlalchemy import DateTime , Boolean , String , func , Integer ,  Column , Text , ForeignKey

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer,primary_key=True)
    title = Column(String(255),nullable=False)
    decription = Column(Text,nullable=True)
    difficulty_level = Column(String(20),nullable=False)
    estimated_hours = Column(Integer,nullable=False)
    is_active = Column(Boolean,nullable=False,default=True)
