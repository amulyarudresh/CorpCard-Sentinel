from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

def seed_data():
    db = SessionLocal()
    try:
        # Seed Policies
        policies = [
            {"rule_name": "No Gambling", "description": "Transactions at casinos, betting sites, or lottery merchants are strictly prohibited."},
            {"rule_name": "Travel Limit", "description": "Single meal expenses during travel cannot exceed $100."},
            {"rule_name": "Tech Equipment", "description": "Computer hardware purchases over $2000 require prior approval."}
        ]

        for p_data in policies:
            exists = db.query(models.Policy).filter_by(rule_name=p_data["rule_name"]).first()
            if not exists:
                policy = models.Policy(rule_name=p_data["rule_name"], description=p_data["description"], is_active=True)
                db.add(policy)
                print(f"Added policy: {p_data['rule_name']}")
            else:
                print(f"Policy already exists: {p_data['rule_name']}")

        # Seed Users
        users = [
            {"name": "Alice Engineering", "email": "alice@corp.com", "card_status": models.CardStatus.ACTIVE},
            {"name": "Bob Sales", "email": "bob@corp.com", "card_status": models.CardStatus.ACTIVE},
            {"name": "Charlie Intern", "email": "charlie@corp.com", "card_status": models.CardStatus.ACTIVE}
        ]

        for u_data in users:
            exists = db.query(models.User).filter_by(name=u_data["name"]).first()
            if not exists:
                user = models.User(name=u_data["name"], email=u_data["email"], card_status=u_data["card_status"])
                db.add(user)
                print(f"Added user: {u_data['name']}")
            else:
                print(f"User already exists: {u_data['name']}")

        db.commit()
        print("Database Seeded Successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
