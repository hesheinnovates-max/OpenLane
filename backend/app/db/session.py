import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in the environment.")

# Hosts like Neon / Render give "postgres://" or "postgresql://" links ,
# SQLAlchemy needs "postgresql+psycopg://" to use the psycopg driver
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://","postgresql+psycopg://",1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://","postgresql+psycopg://",1)

# pool_pre_ping reconnects if the cloud database went to sleep
engine = create_engine(DATABASE_URL,pool_pre_ping=True)

SessionLocal  = sessionmaker(bind=engine,autoflush=False,autocommit=False)

