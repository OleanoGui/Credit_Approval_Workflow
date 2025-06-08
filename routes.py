from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import models

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
def create_user(username: str, role: str, db: Session = Depends(get_db)):
    user = models.User(username=username, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/credit-requests/")
def create_credit_request(user_id: int, amount: float, db: Session = Depends(get_db)):
    credit_request = models.CreditRequest(user_id=user_id, amount=amount)
    db.add(credit_request)
    db.commit()
    db.refresh(credit_request)
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