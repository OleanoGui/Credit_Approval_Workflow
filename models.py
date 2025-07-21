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
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Float, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user = relationship("User")

class ApprovalStage(Base):
    __tablename__ = "approval_stages"
    id = Column(Integer, primary_key=True)
    credit_request_id = Column(Integer, ForeignKey("credit_requests.id"))
    approver_id = Column(Integer, ForeignKey("users.id"), index=True)
    stage = Column(String)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True)
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

class WorkflowStage(Base):
    __tablename__ = "workflow_stages"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Ex: 'analyst', 'manager', 'director'
    order = Column(Integer, nullable=False)  # Ordem da etapa no workflow

class CreditRequestApproval(Base):
    __tablename__ = "credit_request_approvals"
    id = Column(Integer, primary_key=True)
    credit_request_id = Column(Integer, ForeignKey("credit_requests.id"))
    stage_id = Column(Integer, ForeignKey("workflow_stages.id"))
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)

    credit_request = relationship("CreditRequest")
    stage = relationship("WorkflowStage")
    approver = relationship("User")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

