import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app import models
from app.models import utc_now

# In-memory SQLite engine with StaticPool for thread-safe test sharing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Baseline seed data for tests
    db.add_all([
        models.DoorLock(id="front_door", name="Front Door Lock", is_locked=True, last_changed_at=utc_now()),
        models.DoorLock(id="back_door", name="Patio Back Door", is_locked=True, last_changed_at=utc_now()),
        models.DoorLock(id="garage_entry", name="Garage Side Door", is_locked=True, last_changed_at=utc_now()),
        models.GroceryItem(name="Organic Eggs", quantity=12, category="Dairy", is_active=True, created_at=utc_now()),
        models.Reminder(title="Call Mechanic", remind_at="2:00 PM", priority="high", is_active=True, created_at=utc_now()),
    ])
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
