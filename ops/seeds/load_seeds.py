# ops/seeds/load_seeds.py
"""
Loads seed CSV files into DB for quick demo.
"""
import csv
from pathlib import Path
from sqlalchemy import create_engine
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal

def load_csv_to_table(path: Path, table: str):
    import pandas as pd
    df = pd.read_csv(path)
    with engine.connect() as conn:
        df.to_sql(table, con=conn, if_exists="append", index=False)

def run():
    base = Path(__file__).parent
    db = SessionLocal()
    try:
        # create user
        from app.models.user import User
        user = User(email="admin@school.local", hashed_password="fakehash", role="admin")
        db.add(user)
        db.commit()
        # Minimal seeding: students and class_sections table are not fully modeled - just demonstrate
        print("Seed done: admin user created.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
