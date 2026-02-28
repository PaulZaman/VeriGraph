"""
Model Loader for VeriGraph
Loads ML models from DagHub MLflow tracking
"""

import os
import mlflow
import dagshub
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.dagshub_repo = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
        self.model_name = os.getenv("MODEL_NAME", "fact-checker-bert")
        self.model_version = os.getenv("MODEL_VERSION", "1")
        
    def initialize(self):
        """Initialize DagHub and load the model"""
        try:
            # Initialize DagHub
            dagshub.init(
                repo_owner=self.dagshub_repo.split('/')[0],
                repo_name=self.dagshub_repo.split('/')[1],
                mlflow=True
            )
            
            logger.info(f"Connected to DagHub repo: {self.dagshub_repo}")
            
            # Set MLflow tracking URI to DagHub
            mlflow.set_tracking_uri(f"https://dagshub.com/{self.dagshub_repo}.mlflow")
            
            # Try to load from registered model first
            try:
                if self.model_version == "latest":
                    model_uri = f"models:/{self.model_name}/latest"
                else:
                    model_uri = f"models:/{self.model_name}/{self.model_version}"
                
                logger.info(f"Attempting to load model from registry: {model_uri}")
                self.model = mlflow.pyfunc.load_model(model_uri)
                self.model_loaded = True
                logger.info("Model loaded successfully from registry!")
                return
                
            except Exception as registry_error:
                logger.warning(f"Could not load from registry: {str(registry_error)}")
                logger.info("Attempting to load from latest run...")
                
                # Fallback: Try to load from the latest run with logged model
                from mlflow.tracking import MlflowClient
                client = MlflowClient()
                
                # Search for runs with logged models
                experiments = client.search_experiments()
                
                for exp in experiments:
                    if exp.lifecycle_stage == "active":
                        runs = client.search_runs(
                            experiment_ids=[exp.experiment_id],
                            order_by=["start_time DESC"],
                            max_results=10
                        )
                        
                        for run in runs:
                            # Check if run has artifacts (models)
                            try:
                                artifacts = client.list_artifacts(run.info.run_id)
                                for artifact in artifacts:
                                    if artifact.path == "model" or "model" in artifact.path:
                                        model_uri = f"runs:/{run.info.run_id}/{artifact.path}"
                                        logger.info(f"Found model in run {run.info.run_id[:8]}...")
                                        logger.info(f"Loading from: {model_uri}")
                                        self.model = mlflow.pyfunc.load_model(model_uri)
                                        self.model_loaded = True
                                        logger.info("Model loaded successfully from run!")
                                        return
                            except Exception:
                                continue
                
                raise Exception("No models found in registry or recent runs")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            logger.warning("Running in mock mode - predictions will be simulated")
            logger.info("To fix this:")
            logger.info("1. Train and log a model with mlflow.log_model()")
            logger.info("2. Register it with mlflow.register_model()")
            logger.info(f"3. Or update MODEL_NAME in .env to match an existing model")
            logger.info(f"4. Visit: https://dagshub.com/{self.dagshub_repo}/experiments")
            self.model_loaded = False
    
    def predict(self, claim: str) -> dict:
        """Make a prediction on a claim"""
        if not self.model_loaded or self.model is None:
            # Return mock prediction if model not loaded
            logger.warning("Model not loaded, returning mock prediction")
            return {
                "result": "SUPPORTED",
                "confidence": 0.85,
                "mode": "mock"
            }
        
        try:
            # Make actual prediction
            import pandas as pd
            input_data = pd.DataFrame({"claim": [claim]})
            prediction = self.model.predict(input_data)
            
            # Parse prediction results
            # Adjust this based on your model's output format
            result = prediction[0] if isinstance(prediction, list) else prediction
            
            return {
                "result": str(result),
                "confidence": 0.85,  # If your model provides confidence scores, extract them here
                "mode": "live"
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                "result": "ERROR",
                "confidence": 0.0,
                "error": str(e),
                "mode": "error"
            }


# Global model loader instance
model_loader: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """Get or create the global model loader instance"""
    global model_loader
    if model_loader is None:
        model_loader = ModelLoader()
        model_loader.initialize()
    return model_loader
