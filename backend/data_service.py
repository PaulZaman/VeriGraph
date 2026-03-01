"""
Data Service for VeriGraph
Handles model training data queries from Neon DB
"""

import os
import logging
from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

Base = declarative_base()


class TrainingRun(Base):
    """Training runs table - existing in Neon DB"""
    __tablename__ = 'training_runs'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String, nullable=False, index=True)
    model_version = Column(String)
    run_name = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String)
    metrics = Column(JSON)
    created_at = Column(DateTime)


class TrainingData(Base):
    """Training data table - existing in Neon DB"""
    __tablename__ = 'training_data'
    
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=False, index=True)  # Links to training_runs
    claim = Column(Text, nullable=False)
    label = Column(String, nullable=False)
    evidence = Column(JSON)
    created_at = Column(DateTime)


class DataService:
    def __init__(self):
        self.db_url = os.getenv("NEON_DB_URL")
        self.engine = None
        self.Session = None
        
    def initialize(self) -> bool:
        """Initialize database connection"""
        try:
            if not self.db_url:
                logger.error("NEON_DB_URL not set")
                return False
            
            self.engine = create_engine(self.db_url)
            # Don't create tables, they already exist
            # Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            
            logger.info("✅ DataService initialized with Neon DB")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing DataService: {str(e)}")
            return False
    
    def get_model_data(self, model_id: str, limit: int = 100) -> List[Dict]:
        """Get training data for a specific model"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            # Join training_data with training_runs to get data for a specific model
            results = session.query(TrainingData, TrainingRun).join(
                TrainingRun, TrainingData.run_id == TrainingRun.id
            ).filter(
                TrainingRun.model_id == model_id
            ).limit(limit).all()
            
            data = []
            for training_data, training_run in results:
                data.append({
                    "id": training_data.id,
                    "run_id": training_data.run_id,
                    "model_id": training_run.model_id,
                    "model_version": training_run.model_version,
                    "claim": training_data.claim,
                    "label": training_data.label,
                    "evidence": training_data.evidence,
                    "created_at": training_data.created_at.isoformat() if training_data.created_at else None
                })
            
            session.close()
            return data
            
        except Exception as e:
            logger.error(f"Error getting model data: {str(e)}")
            return []
    
    def get_model_stats(self, model_id: str) -> Dict:
        """Get statistics about training data for a model"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            # Get total count for this model
            total = session.query(TrainingData).join(
                TrainingRun, TrainingData.run_id == TrainingRun.id
            ).filter(
                TrainingRun.model_id == model_id
            ).count()
            
            # Count by label
            from sqlalchemy import func
            label_counts = session.query(
                TrainingData.label,
                func.count(TrainingData.id)
            ).join(
                TrainingRun, TrainingData.run_id == TrainingRun.id
            ).filter(
                TrainingRun.model_id == model_id
            ).group_by(TrainingData.label).all()
            
            session.close()
            
            return {
                "model_id": model_id,
                "total_samples": total,
                "label_distribution": {label: count for label, count in label_counts}
            }
            
        except Exception as e:
            logger.error(f"Error getting model stats: {str(e)}")
            return {}
    
    def search_claims(self, model_id: str, query: str, limit: int = 20) -> List[Dict]:
        """Search claims in training data"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            # Search claims for a specific model
            results = session.query(TrainingData, TrainingRun).join(
                TrainingRun, TrainingData.run_id == TrainingRun.id
            ).filter(
                TrainingRun.model_id == model_id,
                TrainingData.claim.ilike(f"%{query}%")
            ).limit(limit).all()
            
            data = []
            for training_data, training_run in results:
                data.append({
                    "id": training_data.id,
                    "run_id": training_data.run_id,
                    "claim": training_data.claim,
                    "label": training_data.label,
                    "evidence": training_data.evidence,
                    "created_at": training_data.created_at.isoformat() if training_data.created_at else None
                })
            
            session.close()
            return data
            
        except Exception as e:
            logger.error(f"Error searching claims: {str(e)}")
            return []


# Singleton instance
_data_service = None


def get_data_service() -> DataService:
    """Get or create singleton DataService instance"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
        _data_service.initialize()
    return _data_service
