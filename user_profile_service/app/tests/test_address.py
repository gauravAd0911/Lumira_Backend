import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_USER_ID = "user-123"


# =========================
# SAMPLE PAYLOAD
# =========================
VALID_ADDRESS = {
    "full_name": "Test User",
    "phone": "9876543210",
    "address_line1": "Street 1",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "is_default": True
}


# =========================
# TEST: CREATE ADDRESS SUCCESS
# =========================
def test_create_address_success(monkeypatch):
    """
    Should create address successfully
    """

    def mock_create_address(db, user_id, data):
        return {**data, "id": "addr-123"}

    monkeypatch.setattr(
        "app.services.address_service.create_address",
        mock_create_address
    )

    response = client.post(
        "/api/v1/users/me/addresses/",
        json=VALID_ADDRESS
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "addr-123"
    assert data["city"] == "Mumbai"


# =========================
# TEST: ADDRESS LIMIT EXCEEDED
# =========================
def test_create_address_limit_exceeded(monkeypatch):
    """
    Should fail when address limit exceeded
    """

    from app.utils.exceptions import AddressLimitExceededException

    def mock_create_address(db, user_id, data):
        raise AddressLimitExceededException(5)

    monkeypatch.setattr(
        "app.services.address_service.create_address",
        mock_create_address
    )

    response = client.post(
        "/api/v1/users/me/addresses/",
        json=VALID_ADDRESS
    )

    assert response.status_code == 400
    assert "Address limit exceeded" in response.json()["detail"]


# =========================
# TEST: INVALID ADDRESS PAYLOAD
# =========================
def test_create_address_invalid_payload():
    """
    Should fail validation (missing required fields)
    """

    invalid_payload = {
        "full_name": "",
        "phone": "123"  # invalid
    }

    response = client.post(
        "/api/v1/users/me/addresses/",
        json=invalid_payload
    )

    # Pydantic validation error
    assert response.status_code == 422


# =========================
# TEST: ADDRESS NOT FOUND (UPDATE)
# =========================
def test_update_address_not_found(monkeypatch):
    """
    Should return 404 when updating non-existing address
    """

    from app.utils.exceptions import AddressNotFoundException

    def mock_update(db, user_id, address_id, data):
        raise AddressNotFoundException()

    monkeypatch.setattr(
        "app.services.address_service.update_address",
        mock_update
    )

    response = client.patch(
        "/api/v1/users/me/addresses/addr-999",
        json=VALID_ADDRESS
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Address not found"


# =========================
# TEST: DELETE ADDRESS SUCCESS
# =========================
def test_delete_address_success(monkeypatch):
    """
    Should delete address successfully
    """

    def mock_delete(db, user_id, address_id):
        return {"message": "Deleted"}

    monkeypatch.setattr(
        "app.services.address_service.delete_address",
        mock_delete
    )

    response = client.delete(
        "/api/v1/users/me/addresses/addr-123"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Deleted"


# =========================
# TEST: SET DEFAULT ADDRESS
# =========================
def test_set_default_address_success(monkeypatch):
    """
    Should set default address
    """

    def mock_set_default(db, user_id, address_id):
        return {"id": address_id, "is_default": True}

    monkeypatch.setattr(
        "app.services.address_service.set_default_address",
        mock_set_default
    )

    response = client.patch(
        "/api/v1/users/me/addresses/addr-123/default"
    )

    assert response.status_code == 200
    assert response.json()["is_default"] is True