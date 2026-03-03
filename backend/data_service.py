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
    
    run_id = Column(Integer, primary_key=True)
    mlflow_run_id = Column(String, index=True)
    model_type = Column(String)
    model_name = Column(String)
    training_started_at = Column(DateTime)
    training_completed_at = Column(DateTime)
    num_training_examples = Column(Integer)
    num_validation_examples = Column(Integer)
    hyperparameters = Column(JSON)
    metrics = Column(JSON)
    status = Column(String)
    notes = Column(Text)


class TrainingData(Base):
    """Training data table - existing in Neon DB"""
    __tablename__ = 'training_data'
    
    data_id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=False, index=True)  # Links to training_runs.run_id
    claim = Column(Text, nullable=False)
    label = Column(String, nullable=False)
    evidence = Column(Text)  # Text not JSON in actual schema
    data_type = Column(String)
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
    
    def get_model_data(self, mlflow_run_id: str = None, model_name: str = None, offset: int = 0, limit: int = 100) -> List[Dict]:
        """Get training data for a specific MLflow run or model name with pagination"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            # Build query
            query = session.query(TrainingData, TrainingRun).join(
                TrainingRun, TrainingData.run_id == TrainingRun.run_id
            )
            
            # Try to filter by mlflow_run_id first
            if mlflow_run_id:
                query = query.filter(TrainingRun.mlflow_run_id == mlflow_run_id)
                results = query.offset(offset).limit(limit).all()
                
                # If no results with mlflow_run_id, fall back to model_name pattern
                if not results and model_name:
                    logger.warning(f"No data found for mlflow_run_id={mlflow_run_id}, trying model_name pattern")
                    query = session.query(TrainingData, TrainingRun).join(
                        TrainingRun, TrainingData.run_id == TrainingRun.run_id
                    ).filter(TrainingRun.model_name.ilike(f"%{model_name}%"))
                    results = query.offset(offset).limit(limit).all()
            elif model_name:
                query = query.filter(TrainingRun.model_name.ilike(f"%{model_name}%"))
                results = query.offset(offset).limit(limit).all()
            else:
                results = query.offset(offset).limit(limit).all()
            
            data = []
            for training_data, training_run in results:
                # Parse evidence - split by newlines if it's a multi-line string
                evidence = [training_data.evidence] if training_data.evidence else []
                
                data.append({
                    "id": training_data.data_id,
                    "run_id": training_data.run_id,
                    "mlflow_run_id": training_run.mlflow_run_id,
                    "model_name": training_run.model_name,
                    "claim": training_data.claim,
                    "label": training_data.label,
                    "evidence": evidence,
                    "created_at": training_data.created_at.isoformat() if training_data.created_at else None
                })
            
            session.close()
            return data
            
        except Exception as e:
            logger.error(f"Error getting model data: {str(e)}")
            return []
    
    def get_model_stats(self, mlflow_run_id: str = None, model_name: str = None) -> Dict:
        """Get statistics about training data for an MLflow run or model name"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            # Build query
            query = session.query(TrainingData).join(
                TrainingRun, TrainingData.run_id == TrainingRun.run_id
            )
            
            # Try to filter by mlflow_run_id first
            if mlflow_run_id:
                query_filtered = query.filter(TrainingRun.mlflow_run_id == mlflow_run_id)
                total = query_filtered.count()
                
                # If no results, fall back to model_name pattern
                if total == 0 and model_name:
                    logger.warning(f"No stats for mlflow_run_id={mlflow_run_id}, using model_name pattern")
                    query_filtered = session.query(TrainingData).join(
                        TrainingRun, TrainingData.run_id == TrainingRun.run_id
                    ).filter(TrainingRun.model_name.ilike(f"%{model_name}%"))
                    total = query_filtered.count()
            elif model_name:
                query_filtered = query.filter(TrainingRun.model_name.ilike(f"%{model_name}%"))
                total = query_filtered.count()
            else:
                query_filtered = query
                total = query_filtered.count()
            
            # Count by label
            from sqlalchemy import func
            label_query = session.query(
                TrainingData.label,
                func.count(TrainingData.data_id)
            ).join(
                TrainingRun, TrainingData.run_id == TrainingRun.run_id
            )
            
            if mlflow_run_id and total > 0:
                label_query = label_query.filter(TrainingRun.mlflow_run_id == mlflow_run_id)
            elif model_name:
                label_query = label_query.filter(TrainingRun.model_name.ilike(f"%{model_name}%"))
            
            label_counts = label_query.group_by(TrainingData.label).all()
            
            session.close()
            
            return {
                "mlflow_run_id": mlflow_run_id,
                "model_name": model_name,
                "total_samples": total,
                "label_distribution": {label: count for label, count in label_counts}
            }
            
        except Exception as e:
            logger.error(f"Error getting model stats: {str(e)}")
            return {}
    
    def search_claims(self, mlflow_run_id: str = None, model_name: str = None, query: str = "", offset: int = 0, limit: int = 20) -> List[Dict]:
        """Search claims in training data for an MLflow run or model name with pagination"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            # Build query
            search_query = session.query(TrainingData, TrainingRun).join(
                TrainingRun, TrainingData.run_id == TrainingRun.run_id
            ).filter(
                TrainingData.claim.ilike(f"%{query}%")
            )
            
            # Try to filter by mlflow_run_id first
            if mlflow_run_id:
                search_query = search_query.filter(TrainingRun.mlflow_run_id == mlflow_run_id)
                results = search_query.offset(offset).limit(limit).all()
                
                # If no results, fall back to model_name pattern
                if not results and model_name:
                    logger.warning(f"No search results for mlflow_run_id={mlflow_run_id}, using model_name pattern")
                    search_query = session.query(TrainingData, TrainingRun).join(
                        TrainingRun, TrainingData.run_id == TrainingRun.run_id
                    ).filter(
                        TrainingData.claim.ilike(f"%{query}%"),
                        TrainingRun.model_name.ilike(f"%{model_name}%")
                    )
                    results = search_query.offset(offset).limit(limit).all()
            elif model_name:
                search_query = search_query.filter(TrainingRun.model_name.ilike(f"%{model_name}%"))
                results = search_query.offset(offset).limit(limit).all()
            else:
                results = search_query.offset(offset).limit(limit).all()
            
            data = []
            for training_data, training_run in results:
                # Parse evidence - split by newlines if it's a multi-line string
                evidence = [training_data.evidence] if training_data.evidence else []
                
                data.append({
                    "id": training_data.data_id,
                    "run_id": training_data.run_id,
                    "claim": training_data.claim,
                    "label": training_data.label,
                    "evidence": evidence,
                    "created_at": training_data.created_at.isoformat() if training_data.created_at else None
                })
            
            session.close()
            return data
            
        except Exception as e:
            logger.error(f"Error searching claims: {str(e)}")
            return []
    
    def get_current_model_data(self, offset: int = 0, limit: int = 20) -> Dict:
        """
        Get training data for the currently active model based on MODEL_STAGE environment
        
        Args:
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            Dict with model_info, data, stats, and pagination info for the current model
        """
        try:
            # Import here to avoid circular dependency
            from mlflow_service import get_mlflow_service
            
            # Get current model info from MLflow
            mlflow_service = get_mlflow_service()
            model_info = mlflow_service.get_current_model_info()
            
            if not model_info:
                logger.error("Could not get current model info from MLflow")
                return {
                    "status": "error",
                    "error": "Could not retrieve current model information from MLflow"
                }
            
            # model_info['model_id'] contains the MLflow run_id
            # model_info['model_name'] contains the model name (e.g., "fact-checker-gan")
            mlflow_run_id = model_info['model_id']
            model_name = model_info['model_name']
            
            # Get training data (with fallback to model name if mlflow_run_id not linked)
            data = self.get_model_data(mlflow_run_id=mlflow_run_id, model_name=model_name, offset=offset, limit=limit)
            
            # Get stats (with fallback) - always get total stats, not paginated
            stats = self.get_model_stats(mlflow_run_id=mlflow_run_id, model_name=model_name)
            
            # Add pagination info
            total_samples = stats.get('total_samples', 0)
            
            return {
                "status": "success",
                "model_info": model_info,
                "data": data,
                "stats": stats,
                "pagination": {
                    "offset": offset,
                    "limit": limit,
                    "total": total_samples,
                    "has_more": (offset + limit) < total_samples
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting current model data: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def search_current_model_data(self, query: str, offset: int = 0, limit: int = 20) -> Dict:
        """
        Search claims in the currently active model's training data
        
        Args:
            query: Search query string
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            Dict with model_info, search results, and pagination info
        """
        try:
            # Import here to avoid circular dependency
            from mlflow_service import get_mlflow_service
            
            # Get current model info from MLflow
            mlflow_service = get_mlflow_service()
            model_info = mlflow_service.get_current_model_info()
            
            if not model_info:
                logger.error("Could not get current model info from MLflow")
                return {
                    "status": "error",
                    "error": "Could not retrieve current model information from MLflow"
                }
            
            mlflow_run_id = model_info['model_id']
            model_name = model_info['model_name']
            
            # Perform search
            results = self.search_claims(
                mlflow_run_id=mlflow_run_id,
                model_name=model_name,
                query=query,
                offset=offset,
                limit=limit
            )
            
            # Get total count for pagination
            # Need to count all matching results
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            count_query = session.query(TrainingData).join(
                TrainingRun, TrainingData.run_id == TrainingRun.run_id
            ).filter(
                TrainingData.claim.ilike(f"%{query}%")
            )
            
            if mlflow_run_id:
                count_query = count_query.filter(TrainingRun.mlflow_run_id == mlflow_run_id)
            
            total_results = count_query.count()
            session.close()
            
            return {
                "status": "success",
                "model_info": model_info,
                "query": query,
                "data": results,
                "pagination": {
                    "offset": offset,
                    "limit": limit,
                    "total": total_results,
                    "has_more": (offset + limit) < total_results
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching current model data: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def list_training_runs(self) -> List[Dict]:
        """List all training runs with their models"""
        try:
            if not self.Session:
                self.initialize()
            
            session = self.Session()
            
            # Get all training runs with data count
            from sqlalchemy import func
            runs = session.query(
                TrainingRun,
                func.count(TrainingData.data_id).label('data_count')
            ).outerjoin(
                TrainingData, TrainingData.run_id == TrainingRun.run_id
            ).group_by(TrainingRun.run_id).order_by(TrainingRun.training_started_at.desc()).all()
            
            result = []
            for run, data_count in runs:
                result.append({
                    "run_id": run.run_id,
                    "mlflow_run_id": run.mlflow_run_id,
                    "model_name": run.model_name,
                    "model_type": run.model_type,
                    "status": run.status,
                    "metrics": run.metrics,
                    "data_count": data_count,
                    "num_training_examples": run.num_training_examples,
                    "num_validation_examples": run.num_validation_examples,
                    "started_at": run.training_started_at.isoformat() if run.training_started_at else None,
                    "completed_at": run.training_completed_at.isoformat() if run.training_completed_at else None
                })
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error listing training runs: {str(e)}")
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
