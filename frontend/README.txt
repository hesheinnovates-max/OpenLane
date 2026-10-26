OpenLane frontend

Pages are served by the FastAPI backend (run uvicorn from the backend folder and open
http://127.0.0.1:8000). Opening the HTML files directly will not work, they need the API.

templates/
    index.html                 Choose Job Seeker or Company
    job-seeker-login.html      Login (email or phone + password)
    job-seeker-register.html   Full name, email OR phone, password
    company-login.html         Login (email or phone + password)
    company-register.html      Company name, email, phone, password
    token-account.html         Forgot password: request a reset code
    reset-password.html        Enter code + new password
    job-seeker-dashboard.html  Learning progress, skill catalogue, jobs, applications, profile
    company-dashboard.html     Overview, job listings, post/edit job, applications, profile
    jobs.html                  Public job listings (no login needed to browse)
    not-found.html             404 page

css/styles.css                 Shared design for every page (desktop and phone)

js/forms.js                    Login / register / reset forms (validation, messages, redirects)
js/app.js                      Shared helpers: API calls, toasts, tabs, modals, progress bars
js/jobs-shared.js              Job cards, job details and apply form
js/company-dashboard.js        Company dashboard
js/job-seeker-dashboard.js     Job Seeker dashboard
js/jobs.js                     Public jobs page

Forms send normal FormData. Browser checks are only for convenience; the backend
validates everything again, hashes passwords and checks who owns each record.
