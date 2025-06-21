# tests/test_schemas.py
import pytest
from schemas import UserCreate, CreditRequestCreate, CreditRequestResponse
from datetime import datetime

def test_user_create_schema_valid():
    data = {"username": "user1", "role": "admin", "password": "pw"}
    user = UserCreate(**data)
    assert user.username == "user1"
    assert user.role == "admin"

def test_user_create_schema_invalid():
    with pytest.raises(TypeError):
        UserCreate(username="user1", password="pw")  # missing role

def test_credit_request_response_schema():
    now = datetime.utcnow()
    data = {
        "id": 1,
        "user_id": 2,
        "amount": 1000.0,
        "status": "pending",
        "created_at": now
    }
    cr = CreditRequestResponse(**data)
    assert cr.amount == 1000.0
    assert cr.status == "pending"