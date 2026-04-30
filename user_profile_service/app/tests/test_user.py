import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_USER_ID = "123e4567-e89b-12d3-a456-426614174000"


class MockUser:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_get_current_user_success(monkeypatch):

    def mock_get_user(db, user_id):
        return MockUser(
            id=MOCK_USER_ID,
            email="test@example.com",
            full_name="Test User",
            phone="9876543210"
        )

    monkeypatch.setattr("app.services.user_service.get_user", mock_get_user)

    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == MOCK_USER_ID


def test_get_current_user_not_found(monkeypatch):
    from app.utils.exceptions import UserNotFoundException

    def mock_get_user(db, user_id):
        raise UserNotFoundException()

    monkeypatch.setattr("app.services.user_service.get_user", mock_get_user)

    response = client.get("/api/v1/users/me")

    assert response.status_code == 404


def test_update_user_success(monkeypatch):

    def mock_update_user(db, user_id, data):
        return {
            "id": MOCK_USER_ID,
            "email": "test@example.com",
            "full_name": getattr(data, "full_name", "Test User"),
            "phone": getattr(data, "phone", "9876543210")
        }

    monkeypatch.setattr("app.services.user_service.update_user", mock_update_user)

    payload = {
        "full_name": "Updated Name",
        "phone": "9999999999"
    }

    response = client.patch("/api/v1/users/me", json=payload)

    assert response.status_code == 200


def test_update_user_invalid_data(monkeypatch):
    from fastapi import HTTPException

    def mock_update_user(db, user_id, data):
        raise HTTPException(status_code=400, detail="Invalid data")

    monkeypatch.setattr("app.services.user_service.update_user", mock_update_user)

    response = client.patch("/api/v1/users/me", json={"full_name": ""})

    assert response.status_code == 400