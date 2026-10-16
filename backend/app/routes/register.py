from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/".."/".."/"frontend"/'templates'

@router.get("/register",response_class=HTMLResponse)
def register():
    return (PAGE/"index.html").read_text("utf-8")

@router.get("/register/company",response_class=HTMLResponse)
def register_company():
    # Register company 
    return {"message":"Register Company works"}

@router.get("/register/job-seeker",response_class=HTMLResponse)
def register_user():
    # Register Job Seeker
    return {"message":"Register Job seeker works"}

