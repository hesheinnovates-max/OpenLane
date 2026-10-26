import os
import sys
from pathlib import Path

import pytest

# Make "import main" and "import app..." work from the project root
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0,str(BACKEND))

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if TEST_DATABASE_URL:
    # Point the app at the test database before it is imported
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ.setdefault("SECRET_KEY","test-secret-key-for-openlane-tests-only-123")
    os.environ["SHOW_RESET_CODE"] = "true"

needs_db = pytest.mark.skipif(not TEST_DATABASE_URL,reason="Set TEST_DATABASE_URL to a throwaway PostgreSQL database to run API tests")

@pytest.fixture(scope="session")
def engine():
    from app.db.session import engine
    from app.db.base import Base
    import app.models
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture()
def client(engine):
    from fastapi.testclient import TestClient
    from app.db.session import SessionLocal
    from app.db.base import Base
    from app.services.seed import seed_skills
    import main

    # Clean every table before each test
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    db = SessionLocal()
    seed_skills(db)
    db.close()

    with TestClient(main.app) as test_client:
        yield test_client

PASSWORD = "Str0ng!Password"

def register_company(client,email="hr@acme.co.za",phone="0821234567",name="Acme Pty Ltd"):
    response = client.post("/company/register",data={"company_name":name,"email":email,"phone":phone,"password":PASSWORD,"confirm_password":PASSWORD})
    assert response.status_code == 200 , response.text
    response = client.post("/company/login",data={"identifier":email,"password":PASSWORD})
    assert response.status_code == 200 , response.text
    return response

def register_job_seeker(client,email="thabo@example.com",name="Thabo Mokoena"):
    response = client.post("/job-seeker/register",data={"full_name":name,"email":email,"phone":"","password":PASSWORD,"confirm_password":PASSWORD})
    assert response.status_code == 200 , response.text
    response = client.post("/job-seeker/login",data={"identifier":email,"password":PASSWORD})
    assert response.status_code == 200 , response.text
    return response
