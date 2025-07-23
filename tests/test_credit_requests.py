from fastapi.testclient import TestClient
from routes import app

client = TestClient(app)

def test_create_credit_request():
    response = client.post("/api/v1/credit-requests/", params={"user_id": 1, "amount": 1000})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["amount"] == 1000

def test_list_credit_requests():
    response = client.get("/api/v1/credit-requests/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)