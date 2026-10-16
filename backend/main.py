from fastapi import FastAPI , Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

app = FastAPI(title="OpenLane ApI",description="API for OpenLane Platform",version="1.0.0")

@app.get("/")
def root():
    return {"message":"Welcome to OpenLane API"}

@app.get("/db-check")
def db_check(db:Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database_connected": result.scalar() == 1}