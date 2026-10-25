OpenLane authentication pages

Files
-----
index.html
    Opening page where the user chooses Job Seeker or Company.

company-login.html
    Company login using email/phone and password.

job-seeker-login.html
    Job Seeker login using email/phone and password.

company-register.html
    Company name, email, phone, and password.

job-seeker-register.html
    Full name, email OR phone, and password.

css/styles.css
    Shared styles used by all five pages.

js/forms.js
    Browser-side checks for contact details and password requirements.


Preview the pages
-----------------
1. Extract this folder into your frontend project.
2. Open index.html using VS Code Live Server.
3. Choose an account type and follow the login/register links.


Backend integration notes
-------------------------
The forms submit regular HTML form data to these routes:

    POST /job-seekers/register
    POST /job-seekers/login
    POST /companies/register
    POST /companies/login

Login forms send fields named `identifier` and `password`. The backend should
accept `identifier` and determine whether it represents an email or phone.

Company registration sends `company_name`, `email`, `phone`, and `password`.
If the SQLAlchemy Company model calls the name field `name`, map `company_name`
to that model field in the backend route.

Job Seeker registration sends `full_name`, `email`, `phone`, and `password`.
The backend model and route must support email OR phone and require at least one.

A regular HTML form expects a browser-friendly response or redirect. If a route
returns JSON, the browser will display that JSON response. JavaScript fetch can
be added later if you want the page to display API responses without navigating.

Browser-side checks are for convenience only. The backend must validate inputs
and hash passwords before saving accounts.
