from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/".."/".."/"frontend"/'templates'

@router.get("/login",response_class=HTMLResponse)
def sign_in():
    return (PAGE/"login.html").read_text(encoding="utf-8")

# ===========================================================
# --------- Sign In Functionality ---------------------------
# ===========================================================


