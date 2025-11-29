from sqlalchemy import create_engine, text
from corpcard_sentinel.database import SQLALCHEMY_DATABASE_URL

def add_violation_reason_column():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as connection:
        try:
            connection.execute(text("ALTER TABLE transactions ADD COLUMN violation_reason TEXT;"))
            print("Successfully added 'violation_reason' column to 'transactions' table.")
        except Exception as e:
            print(f"Error adding column (it might already exist): {e}")

if __name__ == "__main__":
    add_violation_reason_column()
