import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:visa_secret@localhost:3306/corpcard_db")

# Fix for Render: Force pymysql driver if default mysql:// is provided
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    # Import models here to ensure they are registered with Base
    from . import models
    try:
        # Check connection
        with engine.connect() as connection:
            print("Database connection successful.")
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"CRITICAL: Failed to initialize database: {e}")
        raise
