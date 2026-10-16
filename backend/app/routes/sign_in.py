from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/".."/".."/"frontend"/'templates'

@router.get("/sign-in",response_class=HTMLResponse)
def sign_in():
    return {"message":"Sign in works"}

# ===========================================================
# --------- Sign In Functionality ---------------------------
# ===========================================================


