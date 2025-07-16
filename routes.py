import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from schemas import UserResponse
from fastapi.security import OAuth2PasswordRequestForm
from auth import authenticate_user, create_access_token
from datetime import timedelta
from pydantic import BaseModel
from auth import hash_password
from auth import get_current_user
from typing import Optional
from fastapi import Query
import logging
from schemas import CreditRequestResponse
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as aioredis
from fastapi_cache.decorator import cache
from fastapi import APIRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

api_v1 = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROLE_PERMISSIONS = {
    "admin": {"create_user", "approve", "reject", "view_all"},
    "manager": {"approve", "reject", "view_all"},
    "analyst": {"approve", "reject", "view_own"},
}

def has_permission(user, permission):
    return permission in ROLE_PERMISSIONS.get(user.role, set())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_v1.post("/token")
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

@api_v1.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_pw = hash_password(user.password)
    db_user = models.User(username=user.username, role=user.role, password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {db_user.username} (id={db_user.id})")
    return db_user

@api_v1.get("/credit-requests/")
@cache(expire=30)
def list_credit_requests(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime.date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[datetime.date] = Query(None, description="End date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    limit: int = Query(20, ge=1, le=100, description="Limit number of results")  # <-- Adicionado
):
    logger.info("Listagem de solicitações de crédito acessada.")
    query = db.query(models.CreditRequest)
    if status:
        query = query.filter(models.CreditRequest.status == status)
    if user_id:
        query = query.filter(models.CreditRequest.user_id == user_id)
    if start_date:
        query = query.filter(models.CreditRequest.created_at >= start_date)
    if end_date:
        query = query.filter(models.CreditRequest.created_at <= end_date)
    if min_amount is not None:
        query = query.filter(models.CreditRequest.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(models.CreditRequest.amount <= max_amount)
    query = query.order_by(models.CreditRequest.created_at.desc()).limit(limit)
    return [CreditRequestResponse.model_validate(r) for r in query.all()]

@api_v1.get("/credit-requests/{request_id}")
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

@api_v1.get("/admin-only/")
def admin_only_endpoint(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"message": "You are Admin!"}

@api_v1.post("/workflow-stages/")
def create_workflow_stage(name: str, order: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    stage = models.WorkflowStage(name=name, order=order)
    db.add(stage)
    db.commit()
    db.refresh(stage)
    return stage

@api_v1.post("/credit-requests/", response_model=CreditRequestResponse)
def create_credit_request(user_id: int, amount: float, db: Session = Depends(get_db)):
    credit_request = models.CreditRequest(user_id=user_id, amount=amount)
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)

    logger.info(f"Credit request created: id={credit_request.id}, user_id={user_id}, amount={amount}")

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

@api_v1.get("/credit-requests/{credit_request_id}/approvals")
def list_approvals(credit_request_id: int, db: Session = Depends(get_db)):
    approvals = db.query(models.CreditRequestApproval).filter_by(credit_request_id=credit_request_id).all()
    return [
        {
            "id": approval.id,
            "stage": approval.stage.name,
            "status": approval.status.value,
            "approver": approval.approver.username if approval.approver else None,
            "reviewed_at": approval.reviewed_at,
            "rejection_reason": approval.rejection_reason
        }
        for approval in approvals
    ]

@api_v1.post("/credit-requests/{credit_request_id}/approve")
def approve_stage(
    credit_request_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)):

    if not has_permission(current_user, "approve"):
        raise HTTPException(status_code=403, detail="Not authorized")

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

@api_v1.get("/credit-requests/{credit_request_id}/history")
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

@api_v1.post("/credit-requests/{credit_request_id}/reject")
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

@api_v1.get("/users/")
@cache(expire=60)
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not has_permission(current_user, "view_all"):
        raise HTTPException(status_code=403, detail="Not authorized")
    users = db.query(models.User).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]

@api_v1.get("/dashboard/summary")
@cache(expire=60)
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

@api_v1.get("/health")
def healthcheck():
    return {"status": "ok"}

@api_v1.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost:6379", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

Instrumentator().instrument(app).expose(app)
app.include_router(api_v1, prefix="/api/v1")
