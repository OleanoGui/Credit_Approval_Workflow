from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from sqlalchemy import JSON, Column

class CreditRequestCreate(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID must be positive")
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")

    @validator("amount")
    def validate_amount(cls, value):
        if value < 100:
            raise ValueError("Minimum credit request amount is 100")
        return value

class UserPreferences(BaseModel):
    notify_email: bool = True
    notify_sms: bool = False

class UserCreate(BaseModel):
    username: str
    role: str
    password: str
    preferences: UserPreferences = UserPreferences()

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

model_config = {"from_attributes": True}

class CreditRequestCreate(BaseModel):
    user_id: int
    amount: float
    bureau_result = Column(JSON, nullable=True)

class CreditRequestResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    status: str
    created_at: datetime

model_config = {"from_attributes": True}