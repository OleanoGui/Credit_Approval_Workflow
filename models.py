from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import declarative_base, relationship
import enum
import datetime
from database import engine, Base
from sqlalchemy import Boolean
from sqlalchemy import Column, String
from sqlalchemy import Column, Integer, String, Float, Boolean


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
    notify_email = Column(Boolean, default=True)
    notify_sms = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True) 

class CreditRequest(Base):
    __tablename__ = "credit_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Float, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user = relationship("User")
    redit_type = Column(String, nullable=False, default="pessoal")

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
    status = Column(String, default="pending")
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

class WorkflowStage(Base):
    __tablename__ = "workflow_stages"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False) 
    order = Column(Integer, nullable=False)

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

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String, nullable=False)
    credit_request_id = Column(Integer, ForeignKey("credit_requests.id"), index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    ip = Column(String, nullable=True)
    details = Column(String)
    user = relationship("User")
    credit_request = relationship("CreditRequest")

class BusinessRule(Base):
    __tablename__ = "business_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    min_rating = Column(Float, nullable=True)
    min_income = Column(Float, nullable=True)
    block_if_bureau_restriction = Column(Boolean, default=True)

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    notification_type = Column(String, nullable=False)  
    destination = Column(String, nullable=False)        
    status = Column(String, nullable=False)              
    message = Column(Text)
    response = Column(Text)                              
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

