"""
Create database schema for verifications table
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

load_dotenv()

Base = declarative_base()

class Verification(Base):
    """Verification task model"""
    __tablename__ = 'verifications'
    
    id = Column(String, primary_key=True)
    claim = Column(String, nullable=False)
    environment = Column(String, nullable=False)  # 'dev' or 'staging'
    status = Column(String, nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

if __name__ == "__main__":
    db_url = os.getenv("NEON_DB_URL")
    engine = create_engine(db_url)
    
    print("Creating verifications table...")
    Base.metadata.create_all(engine)
    print("✓ Table created successfully!")
