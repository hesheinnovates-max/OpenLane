from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/".."/".."/"frontend"/'templates'

@router.get("/company/add-business",response_class=HTMLResponse)
def add_business():
    # All whats needed for adding a business from A company
    return {"message":"Add Company works"}

# ===========================================================
# --------- Company Functionality ---------------------------
# ===========================================================
