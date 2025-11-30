from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

def seed_data():
    db = SessionLocal()
    try:
        # Realistic Corporate Policies
        policies = [
            {
                "rule_name": "No Gambling", 
                "description": "Transactions at casinos, betting sites, or lottery merchants are strictly prohibited and will result in immediate card freeze."
            },
            {
                "rule_name": "Travel Meal Limit", 
                "description": "Single meal expenses during travel cannot exceed $75. Alcohol is limited to one drink per meal."
            },
            {
                "rule_name": "Tech Procurement", 
                "description": "Computer hardware (Laptops, Monitors) over $500 requires prior IT approval. Peripherals under $100 are allowed."
            },
            {
                "rule_name": "Software Subscriptions", 
                "description": "SaaS subscriptions (e.g., GitHub, AWS) require valid business justification. Personal subscriptions (Netflix, Spotify) are prohibited."
            },
            {
                "rule_name": "Weekend Expense Ban", 
                "description": "Expenses incurred on Saturday or Sunday are flagged for review unless the category is 'Travel' or 'Client Entertainment'."
            },
            {
                "rule_name": "Rideshare Policy", 
                "description": "Uber/Lyft is allowed for business travel. Premium services (Uber Black, Lyft Lux) are prohibited unless transporting clients."
            }
        ]

        print("--- Seeding Policies ---")
        for p_data in policies:
            exists = db.query(models.Policy).filter_by(rule_name=p_data["rule_name"]).first()
            if not exists:
                policy = models.Policy(rule_name=p_data["rule_name"], description=p_data["description"], is_active=True)
                db.add(policy)
                print(f"✅ Added policy: {p_data['rule_name']}")
            else:
                print(f"ℹ️  Policy already exists: {p_data['rule_name']}")

        # Realistic Users
        users = [
            {"name": "Sarah CTO", "email": "sarah.cto@techcorp.com", "card_status": models.CardStatus.ACTIVE},
            {"name": "Mike Sales VP", "email": "mike.sales@techcorp.com", "card_status": models.CardStatus.ACTIVE},
            {"name": "Jessica HR", "email": "jessica.hr@techcorp.com", "card_status": models.CardStatus.ACTIVE},
            {"name": "David Dev", "email": "david.dev@techcorp.com", "card_status": models.CardStatus.ACTIVE},
            {"name": "Emily Intern", "email": "emily.intern@techcorp.com", "card_status": models.CardStatus.ACTIVE},
            {"name": "Alex Marketing", "email": "alex.mkt@techcorp.com", "card_status": models.CardStatus.ACTIVE}
        ]

        print("\n--- Seeding Users ---")
        for u_data in users:
            exists = db.query(models.User).filter_by(name=u_data["name"]).first()
            if not exists:
                user = models.User(name=u_data["name"], email=u_data["email"], card_status=u_data["card_status"])
                db.add(user)
                print(f"✅ Added user: {u_data['name']}")
            else:
                print(f"ℹ️  User already exists: {u_data['name']}")

        db.commit()
        print("\n🎉 Database Seeded Successfully!")
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
