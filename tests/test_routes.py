from fastapi.testclient import TestClient
from routes import app

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/users/",
        json={"username": "testuser", "role": "user", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["role"] == "user"

def test_login():
    client.post(
        "/users/",
        json={"username": "loginuser", "role": "user", "password": "loginpass"}
    )

    response = client.post(
        "/token",
        data={"username": "loginuser", "password": "loginpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()