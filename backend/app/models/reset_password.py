from sqlalchemy import ForeignKey , func , Integer , Boolean , Text , String , Column , DateTime , UniqueConstraint
from app.db.base import Base

# A reset code is valid for this many minutes after it was created
RESET_CODE_MINUTES = 5
# A reset code is blocked after this many wrong attempts
MAX_RESET_ATTEMPTS = 5

class PasswordReset(Base):
    __tablename__ = "password_resets"
    # The same email can belong to a company and a job seeker, so keep one row per account type
    __table_args__ = (
        UniqueConstraint("account_type","email",name="uq_password_reset_type_email"),
        UniqueConstraint("account_type","phone",name="uq_password_reset_type_phone"),
    )
    id = Column(Integer,primary_key=True)
    account_type = Column(String(20),nullable=False)
    phone = Column(String(20),nullable=True)
    email = Column(String(255),nullable=True)
    reset_code = Column(String(255),nullable=False)
    attempts = Column(Integer,nullable=False,default=0)
    used = Column(Boolean,nullable=False,default=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
