import os
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db import Base, get_db
from app.entities import Carrier, Route, User
from app.services.security import hash_password
from app.main import app

# Create in-memory SQLite engine for isolated testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    from app.services.rate_limiter import ai_rate_limiter, generic_rate_limiter
    ai_rate_limiter.reset()
    generic_rate_limiter.reset()

    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed initial test reference data
    c1 = Carrier(carrier_name="Maersk Line", carrier_code="MSK", on_time_pct_hist=80.0)
    c2 = Carrier(carrier_name="CMA CGM", carrier_code="CMA", on_time_pct_hist=60.0)
    r1 = Route(origin_port="Chennai", dest_port="Rotterdam", mode="SEA", avg_transit_days=25.0)
    r2 = Route(origin_port="Bengaluru", dest_port="Frankfurt", mode="AIR", avg_transit_days=3.0)
    u1 = User(name="Ops Manager", email="ops@shipguard.local", password_hash=hash_password("admin123"), role="OPS_USER")

    session.add_all([c1, c2, r1, r2, u1])
    session.commit()

    yield session

    session.close()
    transaction.rollback()
    connection.close()



@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    response = client.post("/api/v1/auth/login", json={"email": "ops@shipguard.local", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
