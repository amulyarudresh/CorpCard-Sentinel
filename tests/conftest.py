import os

# Set dummy API key for testing before importing modules that might use it
os.environ["GOOGLE_API_KEY"] = "dummy_key"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from corpcard_sentinel.database import Base
from corpcard_sentinel.models import User, Policy, Transaction, CardStatus
import datetime

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user(db_session):
    user = User(name="Test User", email="test@example.com", card_status=CardStatus.ACTIVE)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_policy(db_session):
    policy = Policy(rule_name="No Gambling", description="Gambling transactions are forbidden.", is_active=True)
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)
    return policy
