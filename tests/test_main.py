
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from db import Base, get_db
from main import app
import models


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    def get_test_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_save_and_read(client):
    response = client.post("/events", json={
        "source": "web",
        "event_type": "purchase",
        "value": 99.5
    })

    assert response.status_code == 201

    event_id = response.json()["id"]

    stored = client.get(f"/events/{event_id}")

    assert stored.status_code == 200
    assert stored.json()["value"] == 99.5

    metrics = client.get("/metrics").json()
    assert metrics["by_type"]["purchase"] == 1


def test_validation(client):
    response = client.post("/events", json={
        "source": "web",
        "event_type": "purchase",
        "value": -1
    })

    assert response.status_code == 422


def test_not_found(client):
    assert client.get("/events/999").status_code == 404
