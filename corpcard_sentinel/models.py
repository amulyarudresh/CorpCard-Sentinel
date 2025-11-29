from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from .database import Base
import enum
import datetime

class CardStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    card_status = Column(Enum(CardStatus))
    email = Column(String(100))

    transactions = relationship("Transaction", back_populates="user")

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(255))
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    merchant = Column(String(255))
    amount = Column(Float)
    category = Column(String(100))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_violation = Column(Boolean, default=False)
    violation_reason = Column(Text, nullable=True)

    user = relationship("User", back_populates="transactions")
