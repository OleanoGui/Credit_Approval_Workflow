import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from schemas import UserResponse
from tasks import process_credit_request
from fastapi.security import OAuth2PasswordRequestForm
from auth import authenticate_user, create_access_token
from datetime import timedelta
from pydantic import BaseModel
from auth import hash_password
from auth import get_current_user
import logging
from schemas import CreditRequestResponse
from prometheus_fastapi_instrumentator import Instrumentator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserCreate(BaseModel):
    username: str
    role: str
    password: str

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_pw = hash_password(user.password)
    db_user = models.User(username=user.username, role=user.role, password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {db_user.username} (id={db_user.id})")
    return db_user

@app.get("/credit-requests/")
def list_credit_requests(db: Session = Depends(get_db)):
    return db.query(models.CreditRequest).all()

@app.get("/credit-requests/{request_id}")
def get_credit_request_status(request_id: int, db: Session = Depends(get_db)):
    credit_request = db.query(models.CreditRequest).filter(models.CreditRequest.id == request_id).first()
    if not credit_request:
        raise HTTPException(status_code=404, detail="Credit request not found")
    return {
        "id": credit_request.id,
        "status": credit_request.status.value,
        "amount": credit_request.amount,
        "user_id": credit_request.user_id
    }

@app.get("/admin-only/")
def admin_only_endpoint(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"message": "You are Admin!"}

@app.post("/workflow-stages/")
def create_workflow_stage(name: str, order: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    stage = models.WorkflowStage(name=name, order=order)
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage

@app.post("/credit-requests/", response_model=CreditRequestResponse)
def create_credit_request(user_id: int, amount: float, db: Session = Depends(get_db)):
    credit_request = models.CreditRequest(user_id=user_id, amount=amount)
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)

    if amount <= 10000:
        stage_names = ['analyst']
    elif amount <= 50000:
        stage_names = ['analyst', 'manager']
    else:
        stage_names = ['analyst', 'manager', 'director']

    stages = db.query(models.WorkflowStage).filter(models.WorkflowStage.name.in_(stage_names)).order_by(models.WorkflowStage.order).all()
    for stage in stages:
        approval = models.CreditRequestApproval(
            credit_request_id=credit_request.id,
            stage_id=stage.id,
            status=models.ApprovalStatus.PENDING
        )
        db.add(approval)
    db.commit()
    return credit_request

@app.get("/credit-requests/{credit_request_id}/approvals")
def list_approvals(credit_request_id: int, db: Session = Depends(get_db)):
    approvals = db.query(models.CreditRequestApproval).filter_by(credit_request_id=credit_request_id).all()
    return [
        {
            "id": approval.id,
            "stage": approval.stage.name,  # Mostra o nome da etapa
            "status": approval.status.value,
            "approver": approval.approver.username if approval.approver else None,
            "reviewed_at": approval.reviewed_at,
            "rejection_reason": approval.rejection_reason
        }
        for approval in approvals
    ]

@app.post("/credit-requests/{credit_request_id}/approve")
def approve_stage(credit_request_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):

    approval = db.query(models.CreditRequestApproval).join(models.WorkflowStage).filter(
        models.CreditRequestApproval.credit_request_id == credit_request_id,
        models.CreditRequestApproval.status == models.ApprovalStatus.PENDING,
        models.WorkflowStage.name == current_user.role 
    ).order_by(models.WorkflowStage.order).first()

    if not approval:
        raise HTTPException(status_code=403, detail="No pending approval for your role or already approved.")

    approval.status = models.ApprovalStatus.APPROVED
    approval.approver_id = current_user.id
    approval.reviewed_at = datetime.datetime.utcnow()
    db.commit()
    return {"detail": "Stage approved"}

def notify_user(user_email, subject, message):
    logger.info(f"Notify {user_email}: {subject} - {message}")

@app.get("/credit-requests/{credit_request_id}/history")
def approval_history(credit_request_id: int, db: Session = Depends(get_db)):
    approvals = db.query(models.CreditRequestApproval).filter_by(credit_request_id=credit_request_id).all()
    return [
        {
            "stage": approval.stage.name,
            "status": approval.status.value,
            "approver": approval.approver.username if approval.approver else None,
            "reviewed_at": approval.reviewed_at,
            "rejection_reason": getattr(approval, "rejection_reason", None)
        }
        for approval in approvals
    ]

@app.post("/credit-requests/{credit_request_id}/reject")
def reject_stage(
    credit_request_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    approval = db.query(models.CreditRequestApproval).join(models.WorkflowStage).filter(
        models.CreditRequestApproval.credit_request_id == credit_request_id,
        models.CreditRequestApproval.status == models.ApprovalStatus.PENDING,
        models.WorkflowStage.name == current_user.role
    ).order_by(models.WorkflowStage.order).first()

    if not approval:
        raise HTTPException(status_code=403, detail="No pending approval for your role or already rejected.")

    approval.status = models.ApprovalStatus.REJECTED
    approval.approver_id = current_user.id
    approval.reviewed_at = datetime.datetime.utcnow()
    approval.rejection_reason = reason
    db.commit()
    return {"detail": "Stage rejected"}

@app.get("/users/")
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]

@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_requests = db.query(models.CreditRequest).count()
    pending = db.query(models.CreditRequest).filter(models.CreditRequest.status == models.ApprovalStatus.PENDING).count()
    approved = db.query(models.CreditRequest).filter(models.CreditRequest.status == models.ApprovalStatus.APPROVED).count()
    rejected = db.query(models.CreditRequest).filter(models.CreditRequest.status == models.ApprovalStatus.REJECTED).count()
    return {
        "total_requests": total_requests,
        "pending": pending,
        "approved": approved,
        "rejected": rejected
    }

Instrumentator().instrument(app).expose(app)