from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from tasks import process_credit_request
from fastapi.security import OAuth2PasswordRequestForm
from auth import authenticate_user, create_access_token
from datetime import timedelta
from pydantic import BaseModel
from auth import hash_password 

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

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_pw = hash_password(user.password)
    db_user = models.User(username=user.username, role=user.role, password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/credit-requests/")
def create_credit_request(user_id: int, amount: float, db: Session = Depends(get_db)):
    credit_request = models.CreditRequest(user_id=user_id, amount=amount)
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)
    process_credit_request.delay(credit_request.id)
    return credit_request

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