from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum
import datetime
from database import engine, Base


class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    password = Column(String, nullable=False)

class CreditRequest(Base):
    __tablename__ = "credit_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # <-- CORRIGIDO
    user = relationship("User")

class ApprovalStage(Base):
    __tablename__ = "approval_stages"
    id = Column(Integer, primary_key=True)
    credit_request_id = Column(Integer, ForeignKey("credit_requests.id"))
    approver_id = Column(Integer, ForeignKey("users.id"))
    stage = Column(String)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    reviewed_at = Column(DateTime)
    credit_request = relationship("CreditRequest")
    approver = relationship("User")

class CreditRequestWorkflow(Base):
    __tablename__ = "credit_request_workflows"
    id = Column(Integer, primary_key=True)
    credit_request_id = Column(Integer, ForeignKey("credit_requests.id"))
    stage_id = Column(Integer, ForeignKey("approval_stages.id"))
    status = Column(String, default="pending")  # pending, approved, rejected
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

