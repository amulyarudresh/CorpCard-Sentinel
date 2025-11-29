from sqlalchemy.orm import Session
from corpcard_sentinel.database import SessionLocal
from corpcard_sentinel import models

def add_new_policies():
    db = SessionLocal()
    try:
        policies = [
            {"rule_name": "Weekend Ban", "description": "Transactions on Saturday and Sunday are prohibited unless category is Travel."},
            {"rule_name": "Entertainment Limit", "description": "Entertainment expenses cannot exceed $200."},
            {"rule_name": "Suspicious Merchants", "description": "Transactions at 'Unknown Merchant' are flagged."}
        ]

        for p_data in policies:
            exists = db.query(models.Policy).filter_by(rule_name=p_data["rule_name"]).first()
            if not exists:
                policy = models.Policy(rule_name=p_data["rule_name"], description=p_data["description"], is_active=True)
                db.add(policy)
                print(f"Added policy: {p_data['rule_name']}")
            else:
                print(f"Policy already exists: {p_data['rule_name']}")

        db.commit()
        print("New Policies Added Successfully!")
    except Exception as e:
        print(f"Error adding policies: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_new_policies()
