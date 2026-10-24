from pathlib import Path
from fastapi import APIRouter , Form
from fastapi.responses import HTMLResponse

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/".."/".."/"frontend"/'templates'


# ==========================================================
# All get methods for the companies
# ==========================================================

@router.get("/company/add-business",response_class=HTMLResponse)
def add_business():
    # All whats needed for adding a business from A company
    return {"message":"Add Company works"}

@router.get("/company/dashboard",response_class=HTMLResponse)
def company_dashboard():
    return (PAGE/"company-dashboard.html").read_text("uft-8")

@router.get("/company/login",response_class=HTMLResponse)
def company_login():
    return (PAGE/"company-login.html").read_text("uft-8")

# =========================================================
# POST METHODS
# =========================================================

@router.post("/company/login")
def company_login():
    email : str = Form(...)
    password : str = Form(...)

