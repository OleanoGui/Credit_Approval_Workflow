import datetime
import logging
import os
from typing import Optional
from urllib import request

from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import Request
import pyotp
from fastapi import Header

import jwt
import models
from database import SessionLocal
from auth import authenticate_user, create_access_token, get_current_user
from pydantic import BaseModel
from schemas import CreditRequestResponse
import schemas
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as aioredis
from fastapi_cache.decorator import cache
from utils import get_email_template
from notifications import send_email
from prometheus_client import Gauge
import psutil

cpu_usage_gauge = Gauge("cpu_usage_percent", "CPU usage percentage")
memory_usage_gauge = Gauge("memory_usage_mb", "Memory usage in MB")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "refresh_secret")

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

APPROVAL_FLOWS = {
    "pessoal": ["analyst"],
    "empresarial": ["analyst", "manager"],
    "consignado": ["analyst", "manager", "director"]
}

def has_permission(user, permission):
    return permission in ROLE_PERMISSIONS.get(user.role, set())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.middleware("http")
async def prometheus_resource_metrics(request, call_next):
    response = await call_next(request)
    cpu_usage_gauge.set(psutil.cpu_percent())
    memory_usage_gauge.set(psutil.virtual_memory().used / 1024 / 1024)
    return response

def log_audit(db, user_id, action, credit_request_id, details="", ip=None):
    from models import AuditLog
    audit = AuditLog(
        user_id=user_id,
        action=action,
        credit_request_id=credit_request_id,
        details=details,
        ip=ip
    )
    db.add(audit)
    db.commit()

@api_v1.post("/token")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), mfa_code: Optional[str] = None):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if getattr(user, "mfa_enabled", False):
        if not mfa_code:
            raise HTTPException(status_code=400, detail="MFA code required")
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(mfa_code):
            raise HTTPException(status_code=401, detail="Invalid MFA code")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=datetime.timedelta(minutes=30)
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username},
        expires_delta=datetime.timedelta(days=7)
    )
    db = SessionLocal()
    ip = request.client.host if request.client else None
    log_audit(db, user.id, "login", details="User logged in", ip=ip)
    db.close()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

class UserCreate(BaseModel):
    username: str
    role: str
    password: str

@api_v1.post("/refresh")
def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        new_access_token = create_access_token(
            data={"sub": username},
            expires_delta=datetime.timedelta(minutes=30)
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@api_v1.get("/credit-requests/")
@cache(expire=30, namespace=lambda db, status, user_id, start_date, end_date, min_amount, max_amount, limit, current_user=None: f"user:{current_user.id}-status:{status}-min:{min_amount}-max:{max_amount}-limit:{limit}")
def list_credit_requests(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime.date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[datetime.date] = Query(None, description="End date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    limit: int = Query(20, ge=1, le=100, description="Limit number of results"),
    current_user: models.User = Depends(get_current_user)
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

@api_v1.post("/logout")
def logout(request: Request, current_user: models.User = Depends(get_current_user)):
    db = SessionLocal()
    ip = request.client.host if request.client else None
    log_audit(db, current_user.id, "logout", details="User logged out", ip=ip)
    db.close()
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        from auth import blacklist_token
        token = authorization.split(" ")[1]
        blacklist_token(token)
    return {"detail": "Logged out"}

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
def create_credit_request(
    user_id: int, 
    amount: float, 
    credit_type: str,
    db: Session = Depends(get_db)
):
    credit_request = models.CreditRequest(user_id=user_id, amount=amount)
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)
    ip = request.client.host if request.client else None
    log_audit(db, user_id, "create_credit_request", credit_request.id, f"Amount: {amount}", ip=ip)
    logger.info(f"Credit request created: id={credit_request.id}, user_id={user_id}, amount={amount}")

    stage_names = APPROVAL_FLOWS.get(credit_type, ["analyst"])
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


@api_v1.put("/users/{user_id}/preferences")
def update_preferences(user_id: int, preferences: schemas.UserPreferences, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.notify_email = preferences.notify_email
    user.notify_sms = preferences.notify_sms
    db.commit()
    ip = request.client.host if request.client else None
    log_audit(db, current_user.id, "update_preferences", user_id, f"notify_email={preferences.notify_email}, notify_sms={preferences.notify_sms}", ip=ip)
    return {"detail": "Preferences updated"}

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
    ip = request.client.host if request.client else None
    log_audit(db, current_user.id, "approve", credit_request_id, "Stage approved", ip=ip)
    credit_request = db.query(models.CreditRequest).filter_by(id=credit_request_id).first()
    user = db.query(models.User).filter_by(id=credit_request.user_id).first()
    template = get_email_template("approved", credit_request_id)
    send_email(user.email, template["subject"], template["body"])
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
    ip = request.client.host if request.client else None
    log_audit(db, current_user.id, "reject", credit_request_id, f"Reason: {reason}", ip=ip)
    credit_request = db.query(models.CreditRequest).filter_by(id=credit_request_id).first()
    user = db.query(models.User).filter_by(id=credit_request.user_id).first()
    template = get_email_template("rejected", credit_request_id)
    send_email(user.email, template["subject"], template["body"])
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

@api_v1.post("/users/{user_id}/enable-mfa")
def enable_mfa(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = True
    db.commit()
    return {
        "mfa_secret": secret,
        "otpauth_url": pyotp.totp.TOTP(secret).provisioning_uri(user.username, issuer_name="CreditWorkflow")
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
