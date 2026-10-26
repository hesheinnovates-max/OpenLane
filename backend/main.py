from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI , Depends , Request
from fastapi.responses import HTMLResponse , JSONResponse , RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.db.dependencies import get_db
from app.services.auth import read_session , ROLE_COMPANY , ROLE_JOB_SEEKER
from app.services.seed import seed_if_empty

# --------- Include all the routes --------- 
from app.routes import sign_in
from app.routes import job_seekers
from app.routes import companies
from app.routes import register
from app.routes import jobs

@asynccontextmanager
async def lifespan(app : FastAPI):
    # Fill the skill catalogue the first time the app runs
    seed_if_empty()
    yield

app = FastAPI(title="OpenLane ApI",description="API for OpenLane Platform",version="1.0.0",lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------- Include the routes ------------
app.include_router(sign_in.router)
app.include_router(job_seekers.router)
app.include_router(companies.router)
app.include_router(register.router)
app.include_router(jobs.router)


# Find project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSS_DIR = PROJECT_ROOT/"frontend"/'css'
JS_DIR = PROJECT_ROOT/"frontend"/'js'

app.mount("/css",StaticFiles(directory=CSS_DIR),name="css")
app.mount("/js",StaticFiles(directory=JS_DIR),name="js")

PAGE = PROJECT_ROOT/"frontend"/'templates'


# --------- Friendly error messages ------------

@app.exception_handler(RequestValidationError)
def validation_error(request : Request,exc : RequestValidationError):
    # Turn FastAPI's validation list into one plain sentence for the forms
    errors = exc.errors()
    detail = "Please fill in all the required fields"
    if errors:
        field = str(errors[0].get("loc",["",""])[-1]).replace("_"," ")
        if errors[0].get("type") == "missing":
            detail = f"{field.capitalize()} is required"
        else:
            detail = f"{field.capitalize()} is not valid"
    return JSONResponse(status_code=422,content={"detail":detail})

@app.exception_handler(StarletteHTTPException)
def http_error(request : Request,exc : StarletteHTTPException):
    # Show a friendly page when someone opens a page that does not exist in the browser
    wants_html = "text/html" in request.headers.get("accept","")
    if exc.status_code == 404 and wants_html and not request.url.path.startswith("/api/"):
        return HTMLResponse((PAGE/"not-found.html").read_text(encoding="utf-8"),status_code=404)
    return JSONResponse(status_code=exc.status_code,content={"detail":exc.detail},headers=getattr(exc,"headers",None))


@app.get("/",response_class=HTMLResponse)
def root(request : Request):
    # Logged in users go straight to their dashboard
    session = read_session(request)
    if session and session["role"] == ROLE_COMPANY:
        return RedirectResponse("/company/dashboard",status_code=303)
    if session and session["role"] == ROLE_JOB_SEEKER:
        return RedirectResponse("/job-seeker/dashboard",status_code=303)
    return (PAGE/"index.html").read_text(encoding="utf-8")

@app.get("/db-check",response_class=JSONResponse)
def db_check(db:Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database_connected": result.scalar() == 1}
