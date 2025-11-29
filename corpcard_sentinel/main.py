from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, database

app = FastAPI()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    database.init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to CorpCard Sentinel"}

# User Management
@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(name=user.name, email=user.email, card_status=user.card_status)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.post("/users/{user_id}/unfreeze", response_model=schemas.User)
def unfreeze_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.card_status = models.CardStatus.ACTIVE
    db.commit()
    db.refresh(db_user)
    return db_user

# Policy CRUD
@app.post("/policies", response_model=schemas.Policy)
def create_policy(policy: schemas.PolicyCreate, db: Session = Depends(get_db)):
    db_policy = models.Policy(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy

@app.get("/policies", response_model=List[schemas.Policy])
def read_policies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    policies = db.query(models.Policy).filter(models.Policy.is_active == True).offset(skip).limit(limit).all()
    return policies

@app.put("/policies/{policy_id}", response_model=schemas.Policy)
def update_policy(policy_id: int, policy: schemas.PolicyUpdate, db: Session = Depends(get_db)):
    db_policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    for key, value in policy.dict().items():
        setattr(db_policy, key, value)
    
    db.commit()
    db.refresh(db_policy)
    return db_policy

@app.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    db_policy = db.query(models.Policy).filter(models.Policy.id == policy_id).first()
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(db_policy)
    db.commit()
    return {"ok": True}

# Transaction Trigger
@app.post("/simulate_transaction", response_model=schemas.Transaction)
def simulate_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # 1. Check User Status First
    db_user = db.query(models.User).filter(models.User.id == transaction.user_id).first()
    if db_user and db_user.card_status == models.CardStatus.FROZEN:
        # Record the attempted transaction as a violation
        db_transaction = models.Transaction(**transaction.dict())
        db_transaction.is_violation = True
        db_transaction.violation_reason = "Card is FROZEN"
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    # 2. Save transaction first
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # 2. Run Policy Enforcement Graph
    # We convert the ORM model to a dict for the graph
    transaction_dict = {
        "id": db_transaction.id,
        "user_id": db_transaction.user_id,
        "merchant": db_transaction.merchant,
        "amount": db_transaction.amount,
        "category": db_transaction.category,
        "timestamp": db_transaction.timestamp,
        "is_violation": db_transaction.is_violation
    }
    
    from . import sentinel_agent
    result = sentinel_agent.run_transaction_check(transaction_dict)
    
    # 3. Update transaction if violation found (optional, but good for record keeping)
    # The agent 'enforce' node already updates the DB, but we should refresh our object to return the latest state
    # 3. Update transaction with analysis results
    # Always update violation_reason to capture the analysis even if allowed
    db_transaction.is_violation = result.get('is_violation', False)
    db_transaction.violation_reason = result.get('violation_reason')
    db.commit()
    db.refresh(db_transaction)
    
    print(f"DEBUG: Returning transaction: {db_transaction.violation_reason}")
    return db_transaction

@app.get("/transactions", response_model=List[schemas.Transaction])
def read_transactions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    from sqlalchemy import desc
    transactions = db.query(models.Transaction).order_by(desc(models.Transaction.timestamp)).offset(skip).limit(limit).all()
    return transactions
