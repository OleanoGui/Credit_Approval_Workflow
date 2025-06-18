import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, CreditRequest, ApprovalStatus

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_create_user(db_session):
    user = User(username="testuser", role="analyst", password="hashed")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None

def test_create_credit_request(db_session):
    user = User(username="testuser2", role="analyst", password="hashed")
    db_session.add(user)
    db_session.commit()
    cr = CreditRequest(user_id=user.id, amount=1000)
    db_session.add(cr)
    db_session.commit()
    assert cr.status == ApprovalStatus.PENDING
    assert cr.user_id == user.id