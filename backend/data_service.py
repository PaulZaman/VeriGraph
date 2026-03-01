"""
Data Service for VeriGraph
Handles model training data queries from Neon DB
"""

import os
import logging
from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

Base = declarative_base()


class ModelTrainingData(Base):
    """Model training data stored in Neon DB"""
    __tablename__ = 'model_training_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String, nullable=False, index=True)  # Links to MLflow model
    model_version = Column(String, nullable=False)
    claim = Column(Text, nullable=False)
    label = Column(String, nullable=False)  # SUPPORTED, REFUTED, NOT ENOUGH INFO
    evidence = Column(JSON, nullable=True)  # List of evidence texts
    metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime, nullable=False)


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
            Base.metadata.create_all(self.engine)
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
            data = session.query(ModelTrainingData).filter(
                ModelTrainingData.model_id == model_id
            ).limit(limit).all()
            
            result = []
            for item in data:
                result.append({
                    "id": item.id,
                    "model_id": item.model_id,
                    "model_version": item.model_version,
                    "claim": item.claim,
                    "label": item.label,
                    "evidence": item.evidence,
                    "metadata": item.metadata,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                })
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting model data: {str(e)}")
            return []
    
    def get_model_stats(self, model_id: str) -> Dict:
        """Get statistics about training data for a model"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            total = session.query(ModelTrainingData).filter(
                ModelTrainingData.model_id == model_id
            ).count()
            
            # Count by label
            from sqlalchemy import func
            label_counts = session.query(
                ModelTrainingData.label,
                func.count(ModelTrainingData.id)
            ).filter(
                ModelTrainingData.model_id == model_id
            ).group_by(ModelTrainingData.label).all()
            
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
            
            # Simple text search (can be enhanced with full-text search)
            data = session.query(ModelTrainingData).filter(
                ModelTrainingData.model_id == model_id,
                ModelTrainingData.claim.ilike(f"%{query}%")
            ).limit(limit).all()
            
            result = []
            for item in data:
                result.append({
                    "id": item.id,
                    "claim": item.claim,
                    "label": item.label,
                    "evidence": item.evidence,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                })
            
            session.close()
            return result
            
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
