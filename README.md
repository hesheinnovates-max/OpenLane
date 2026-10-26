# OpenLane

A digital skills and employment opportunity platform (FastAPI + PostgreSQL + HTML/CSS/JS).

- **Job Seekers** pick skills from a catalogue, tick off learning steps, see their progress
  (Not Started / In Progress / Completed and a %), browse published jobs and apply.
- **Companies** manage their profile and businesses/branches, post jobs (draft → published → closed),
  edit them and review applications.

## Run it

```bash
# 1. From the OpenLane folder, create / activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# 2. Settings
cp .env.example .env               # then edit DATABASE_URL and SECRET_KEY

# 3. Create / update the database tables (run from the OpenLane folder)
alembic upgrade head

# 4. Start the server (run from the backend folder)
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

The skill catalogue is filled automatically the first time the server starts.
To add more skills, edit `backend/app/services/seed.py` and run `python -m app.services.seed` from the `backend` folder.

## Main pages

| Page | URL |
| --- | --- |
| Choose account type | `/` |
| Job Seeker login / register | `/job-seeker/login`, `/job-seeker/register` |
| Company login / register | `/company/login`, `/company/register` |
| Forgot / reset password | `/forgot-password`, `/password-reset` |
| Job Seeker dashboard | `/job-seeker/dashboard` |
| Company dashboard | `/company/dashboard` |
| Public job listings | `/jobs` |
| API docs | `/docs` |

## Deploy (Render + Neon + Brevo)

Never upload `.env`. It is in `.gitignore`. Put the values in Render's **Environment** page instead.

1. **Database (Neon):** create a project at neon.com and copy the connection string
   (`postgresql://...neon.tech/neondb?sslmode=require`).
2. **Email (Brevo):** create an account at brevo.com, verify your sender email under
   *Senders, Domains & Dedicated IPs*, then create an API key under *SMTP & API → API Keys*.
3. **App (Render):** push the project to GitHub, then on render.com choose
   *New → Web Service* and pick the repo.
   - Root directory: leave empty
   - Build command: `pip install -r backend/requirements.txt && alembic upgrade head`
   - Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment variables: `DATABASE_URL`, `SECRET_KEY`, `COOKIE_SECURE=true`,
     `SHOW_RESET_CODE=false`, `BREVO_API_KEY`, `MAIL_FROM_EMAIL`, `MAIL_FROM_NAME=OpenLane`,
     `PYTHON_VERSION=3.12.3`

Render's free plan blocks SMTP ports (so Gmail SMTP will not work there). That is why the
Brevo API, which uses HTTPS, is used for email in production.

## Password reset

`/forgot-password` creates a 6-digit code (only its hash is stored). It is valid for 5 minutes
(checked by the database with `func.now()`), allows 5 wrong attempts and can only be used once.
The code is always emailed to the address saved on the account (even if the user typed their
phone number). Email goes through Brevo when `BREVO_API_KEY` is set, through SMTP when
`SMTP_HOST` is set, and is otherwise printed in the server terminal. If email is set up but the
email fails, the user sees an error instead of a false "sent" message. Accounts with only a
phone number cannot reset by email yet (SMS is not set up).
With `SHOW_RESET_CODE=true` (development only) it is also shown on screen.

## Tests

```bash
pytest tests/test_progress_rules.py                 # progress % rules, no database needed
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/openlane_test pytest tests
```

Use an empty, throwaway database for `TEST_DATABASE_URL` — the tests delete its data.
