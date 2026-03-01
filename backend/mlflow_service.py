"""
MLflow Service for VeriGraph
Queries MLflow registry to get current model information based on environment stage
"""

import os
import logging
import mlflow
from mlflow.tracking import MlflowClient
from typing import Optional, Dict
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class MLflowService:
    def __init__(self):
        self.dagshub_repo = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
        self.dagshub_user = os.getenv("DAGSHUB_USER", "MarcoSrhl")
        self.dagshub_token = os.getenv("DAGSHUB_TOKEN")
        self.model_name = os.getenv("MODEL_NAME", "fact-checker-bert")
        self.model_stage = os.getenv("MODEL_STAGE", "Staging")
        self.client = None
        
    def initialize(self) -> bool:
        """Initialize MLflow client connection"""
        try:
            if not self.dagshub_token:
                logger.warning("DAGSHUB_TOKEN not set - model registry queries may fail")
                return False
            
            # Set up authentication
            os.environ['MLFLOW_TRACKING_USERNAME'] = self.dagshub_user
            os.environ['MLFLOW_TRACKING_PASSWORD'] = self.dagshub_token
            
            # Set tracking URI
            tracking_uri = f"https://dagshub.com/{self.dagshub_repo}.mlflow"
            mlflow.set_tracking_uri(tracking_uri)
            
            self.client = MlflowClient()
            logger.info(f"✅ MLflowService initialized for {self.model_name} @ {self.model_stage}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MLflowService: {str(e)}")
            return False
    
    def get_current_model_info(self) -> Optional[Dict]:
        """
        Get information about the current model based on MODEL_STAGE environment variable
        
        Returns:
            Dict with model_id (run_id), version, stage, and model_name
            None if not found or error
        """
        try:
            if not self.client:
                if not self.initialize():
                    return None
            
            logger.info(f"Querying {self.model_name} models in {self.model_stage} stage...")
            
            # Get model versions for the specified stage
            versions = self.client.search_model_versions(f"name='{self.model_name}'")
            stage_versions = [v for v in versions if v.current_stage == self.model_stage]
            
            if len(stage_versions) == 0:
                logger.warning(f"No models found in {self.model_stage} stage for '{self.model_name}'")
                return None
            
            if len(stage_versions) > 1:
                logger.warning(f"Multiple models in {self.model_stage} stage - using first one")
            
            # Get the model version
            stage_version = stage_versions[0]
            
            model_info = {
                "model_id": stage_version.run_id,  # This is the MLflow run_id
                "model_name": self.model_name,
                "version": stage_version.version,
                "stage": self.model_stage,
                "status": stage_version.status,
                "description": stage_version.description
            }
            
            logger.info(f"✓ Found model: v{model_info['version']} (run_id: {model_info['model_id'][:8]}...)")
            return model_info
            
        except Exception as e:
            logger.error(f"Error getting current model info: {str(e)}")
            return None


# Singleton instance
_mlflow_service = None

def get_mlflow_service() -> MLflowService:
    """Get or create MLflowService singleton"""
    global _mlflow_service
    if _mlflow_service is None:
        _mlflow_service = MLflowService()
        _mlflow_service.initialize()
    return _mlflow_service
