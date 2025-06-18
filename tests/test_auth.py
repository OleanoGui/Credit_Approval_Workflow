import pytest
from auth import hash_password, verify_password, create_access_token, authenticate_user
from models import User, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import timedelta
import os

@pytest.fixture
def db_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    monkeypatch.setattr("auth.SessionLocal", lambda: session)
    yield session
    session.close()

def test_hash_and_verify_password():
    password = "mysecret"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(minutes=1))
    assert isinstance(token, str)
    assert len(token) > 0

def test_authenticate_user_success(db_session):
    user = User(username="testuser", role="analyst", password=hash_password("pw"))
    db_session.add(user)
    db_session.commit()
    authenticated = authenticate_user("testuser", "pw")
    assert authenticated is not None
    assert authenticated.username == "testuser"

def test_authenticate_user_fail(db_session):
    user = User(username="testuser2", role="analyst", password=hash_password("pw"))
    db_session.add(user)
    db_session.commit()
    assert authenticate_user("testuser2", "wrongpw") is None
    assert authenticate_user("notfound", "pw") is None