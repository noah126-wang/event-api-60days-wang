from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from main import app, get_db


@pytest.fixture
def client_and_session():
    session = Mock(spec=Session)
    app.dependency_overrides[get_db] = lambda: session
    try:
        yield TestClient(app), session
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_db_health_connected(client_and_session):
    client, session = client_and_session

    response = client.get("/db-health")

    assert response.status_code == 200
    assert response.json() == {"database": "connected"}
    session.execute.assert_called_once()
    assert str(session.execute.call_args.args[0]) == "SELECT 1"


def test_db_health_unavailable(client_and_session):
    client, session = client_and_session
    session.execute.side_effect = OperationalError(
        "SELECT 1", {}, ConnectionError("Database unavailable")
    )

    response = client.get("/db-health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}