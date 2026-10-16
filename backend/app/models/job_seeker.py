from sqlalchemy import Boolean , Column , DateTime , Integer , String , func

from app.db.base import Base


class JobSeeker(Base):
    __tablename__ = "job_seekers"

    id = Column(Integer,primary_key=True)
    full_name = Column(String(150),nullable=False)
    email = Column(String(255),unique=True,nullable=False)
    password_hash = Column(String(255),nullable=False)
    is_active = Column(Boolean,nullable=False,default=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
