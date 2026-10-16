from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAGE = PROJECT_ROOT/".."/".."/"frontend"/'templates'

@router.get("/job-seekers",response_class=HTMLResponse)
def test_job_seekers():
    return {"message":"Job Seeker routes are working"}

# ===========================================================
# ------------ Job Seeker Functionality ---------------------
# ===========================================================




