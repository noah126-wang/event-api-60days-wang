
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_event():
    response = client.post("/events", json={
        "source": "web",
        "event_type": "click",
        "value": 10
    })
    assert response.status_code == 201
    assert response.json()["event_type"] == "click"

def test_negative_value():
    response = client.post("/events", json={
        "source": "web",
        "event_type": "purchase",
        "value": -50
    })
    assert response.status_code == 422
