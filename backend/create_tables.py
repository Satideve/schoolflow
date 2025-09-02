import os
from sqlalchemy import create_engine
from app.db.base import Base  # Import your declarative base
from app.core.config import settings  # Import your settings if available

# Load database URL from environment or fallback
db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://admin:admin@localhost:5432/schoolflow")

engine = create_engine(db_url)

def main():
    print(f"Connecting to DB: {db_url}")
    Base.metadata.create_all(engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    main()