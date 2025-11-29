from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class CardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"

# User Schemas
class UserBase(BaseModel):
    name: str
    card_status: CardStatus
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

# Policy Schemas
class PolicyBase(BaseModel):
    rule_name: str
    description: Optional[str] = None
    is_active: bool = True

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(PolicyBase):
    pass

class Policy(PolicyBase):
    id: int

    class Config:
        orm_mode = True

# Transaction Schemas
class TransactionBase(BaseModel):
    user_id: int
    merchant: str
    amount: float
    category: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_violation: bool = False
    violation_reason: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int

    class Config:
        orm_mode = True
