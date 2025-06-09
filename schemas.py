from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    role: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

model_config = {"from_attributes": True}

class CreditRequestCreate(BaseModel):
    user_id: int
    amount: float

class CreditRequestResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    status: str
    created_at: datetime

model_config = {"from_attributes": True}