from conftest import needs_db , register_company , register_job_seeker , PASSWORD

pytestmark = needs_db

def add_job(client,status="published",title="Junior Data Capturer"):
    response = client.post("/api/company/jobs",data={
        "title":title,
        "description":"Capture invoices into our system.",
        "requirements":"Spreadsheets (Excel / Google Sheets), attention to detail",
        "job_type":"Full-time",
        "location":"Johannesburg",
        "status":status,
    })
    assert response.status_code == 200 , response.text
    return response.json()["job"]

def test_role_selection_and_dashboards(client):
    register_company(client)
    assert client.get("/company/dashboard",follow_redirects=False).status_code == 200
    # A company cannot use job seeker pages or actions
    assert client.get("/job-seeker/dashboard",follow_redirects=False).status_code == 303
    assert client.get("/api/job-seeker/skills").status_code == 401
    client.get("/logout")
    register_job_seeker(client)
    assert client.get("/job-seeker/dashboard",follow_redirects=False).status_code == 200
    assert client.get("/api/company/jobs").status_code == 401

def test_wrong_password_and_validation_errors(client):
    register_company(client)
    client.get("/logout")
    response = client.post("/company/login",data={"identifier":"hr@acme.co.za","password":"wrong"})
    assert response.status_code == 409
    response = client.post("/company/register",data={"company_name":"X","email":"bad","phone":"123","password":"weak"})
    assert response.status_code == 409
    response = client.post("/company/register",data={"company_name":"X"})
    assert response.status_code == 422
    assert "required" in response.json()["detail"]

def test_phone_login_with_spaces(client):
    register_company(client,phone="082 555 1234")
    client.get("/logout")
    response = client.post("/company/login",data={"identifier":"+27825551234","password":PASSWORD})
    assert response.status_code == 200

def test_skill_selection_once_and_progress(client):
    register_job_seeker(client)
    skills = client.get("/api/skills").json()
    excel = [s for s in skills if s["name"].startswith("Spreadsheets")][0]
    response = client.post("/api/job-seeker/skills",data={"skill_id":excel["id"]})
    assert response.status_code == 200
    selected = response.json()["skill"]
    assert selected["status"] == "Not Started" and selected["display_percentage"] == 0
    # The same skill cannot be added twice
    assert client.post("/api/job-seeker/skills",data={"skill_id":excel["id"]}).status_code == 409

    # Starting changes the state to In Progress
    started = client.post(f"/api/job-seeker/skills/{selected['id']}/start").json()["skill"]
    assert started["status"] == "In Progress"

    steps = started["steps"]
    for step in steps:
        result = client.patch(f"/api/job-seeker/skills/{selected['id']}/steps/{step['id']}",data={"completed":"true"}).json()
    assert result["skill"]["status"] == "Completed"
    assert result["skill"]["display_percentage"] == 100
    # Un-ticking a step moves it back to In Progress
    result = client.patch(f"/api/job-seeker/skills/{selected['id']}/steps/{steps[0]['id']}",data={"completed":"false"}).json()
    assert result["skill"]["status"] == "In Progress"

def test_overall_progress_average(client):
    register_job_seeker(client)
    skills = client.get("/api/skills").json()
    # Pick three skills with an even number of steps so 50% is exact
    chosen = [s for s in skills if s["steps_count"] in (4,6,8)][:3]
    ids = []
    for skill in chosen:
        ids.append(client.post("/api/job-seeker/skills",data={"skill_id":skill["id"]}).json()["skill"])
    # 100% on the first , 50% on the second , 0% on the third
    for step in ids[0]["steps"]:
        client.patch(f"/api/job-seeker/skills/{ids[0]['id']}/steps/{step['id']}",data={"completed":"true"})
    half = ids[1]["steps"][: len(ids[1]["steps"]) // 2]
    for step in half:
        result = client.patch(f"/api/job-seeker/skills/{ids[1]['id']}/steps/{step['id']}",data={"completed":"true"}).json()
    assert result["overall"]["display_percentage"] == 50

def test_learner_cannot_change_another_learners_progress(client):
    register_job_seeker(client)
    skill = client.get("/api/skills").json()[0]
    mine = client.post("/api/job-seeker/skills",data={"skill_id":skill["id"]}).json()["skill"]
    client.get("/logout")
    register_job_seeker(client,email="other@example.com",name="Other Person")
    response = client.patch(f"/api/job-seeker/skills/{mine['id']}/steps/{mine['steps'][0]['id']}",data={"completed":"true"})
    assert response.status_code == 404

def test_company_profile_and_publishing(client):
    register_company(client)
    response = client.put("/api/company/profile",data={"company_name":"Acme","email":"hr@acme.co.za","phone":"0821234567","alt_phone":"011 555 0000","description":"We build things"})
    assert response.status_code == 200
    assert response.json()["company"]["alt_phone"] == "0115550000"

    draft = add_job(client,status="draft",title="Draft job")
    published = add_job(client,status="published",title="Published job")
    titles = [job["title"] for job in client.get("/api/jobs").json()["jobs"]]
    assert "Published job" in titles and "Draft job" not in titles
    assert client.get(f"/api/jobs/{draft['id']}").status_code == 404

    # Close it , it disappears from public discovery
    client.patch(f"/api/company/jobs/{published['id']}/status",data={"status":"closed"})
    assert client.get("/api/jobs").json()["jobs"] == []

    # Edit
    response = client.put(f"/api/company/jobs/{draft['id']}",data={"title":"Edited","description":"d","requirements":"r","status":"published"})
    assert response.json()["job"]["title"] == "Edited"

def test_ownership(client):
    register_company(client)
    job = add_job(client)
    client.get("/logout")
    register_company(client,email="other@corp.co.za",phone="0831112222",name="Other")
    assert client.put(f"/api/company/jobs/{job['id']}",data={"title":"Hacked","description":"d","requirements":"r"}).status_code == 404
    assert client.patch(f"/api/company/jobs/{job['id']}/status",data={"status":"closed"}).status_code == 404
    assert client.delete(f"/api/company/jobs/{job['id']}").status_code == 404

def test_applications_flow(client):
    register_company(client)
    job = add_job(client)
    client.get("/logout")
    register_job_seeker(client)
    response = client.post(f"/api/jobs/{job['id']}/apply",data={"message":"I would love this job"})
    assert response.status_code == 200
    assert client.post(f"/api/jobs/{job['id']}/apply",data={"message":"again"}).status_code == 409
    mine = client.get("/api/job-seeker/applications").json()
    assert mine[0]["job"]["title"] == "Junior Data Capturer"
    client.get("/logout")
    client.post("/company/login",data={"identifier":"hr@acme.co.za","password":PASSWORD})
    applications = client.get("/api/company/applications").json()
    assert applications[0]["applicant"]["full_name"] == "Thabo Mokoena"
    response = client.patch(f"/api/company/applications/{applications[0]['id']}/status",data={"status":"shortlisted"})
    assert response.status_code == 200
    assert client.get("/api/company/overview").json()["stats"]["applications"] == 1
    # A job with applications cannot be deleted , only closed
    assert client.delete(f"/api/company/jobs/{job['id']}").status_code == 409

def test_password_reset(client):
    register_job_seeker(client)
    client.get("/logout")
    response = client.post("/forgot-password",data={"detail":"thabo@example.com","account_type":"job_seeker"})
    assert response.status_code == 200
    code = response.json()["message"].split("code: ")[1].rstrip(")")
    new_password = "N3w!Password-2026"
    wrong = client.post("/password-reset",data={"detail":"thabo@example.com","account_type":"job_seeker","reset_token":"000000" if code != "000000" else "111111","new_password":new_password,"confirm_password":new_password})
    assert wrong.status_code == 409
    ok = client.post("/password-reset",data={"detail":"thabo@example.com","account_type":"job_seeker","reset_token":code,"new_password":new_password,"confirm_password":new_password})
    assert ok.status_code == 200 , ok.text
    # The code can only be used once
    again = client.post("/password-reset",data={"detail":"thabo@example.com","account_type":"job_seeker","reset_token":code,"new_password":new_password,"confirm_password":new_password})
    assert again.status_code == 409
    assert client.post("/job-seeker/login",data={"identifier":"thabo@example.com","password":new_password}).status_code == 200

def test_persistence_after_logout(client):
    register_job_seeker(client)
    skill = client.get("/api/skills").json()[0]
    selected = client.post("/api/job-seeker/skills",data={"skill_id":skill["id"]}).json()["skill"]
    client.patch(f"/api/job-seeker/skills/{selected['id']}/steps/{selected['steps'][0]['id']}",data={"completed":"true"})
    client.get("/logout")
    client.post("/job-seeker/login",data={"identifier":"thabo@example.com","password":PASSWORD})
    skills = client.get("/api/job-seeker/skills").json()["skills"]
    assert skills[0]["completed_steps"] == 1
