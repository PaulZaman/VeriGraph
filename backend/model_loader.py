"""
Model Loader for VeriGraph
Loads ML models from DagHub MLflow tracking
"""

import os
import mlflow
from typing import Optional
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.dagshub_repo = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
        self.model_name = os.getenv("MODEL_NAME", "fact-checker-bert")
        self.model_version = os.getenv("MODEL_VERSION", "1")
        self.label_map = {0: "SUPPORTS", 1: "REFUTES", 2: "NOT ENOUGH INFO"}
        
    def initialize(self):
        """Initialize DagHub and load the model"""
        try:
            # For public repos, we don't need dagshub.init()
            # Just set the MLflow tracking URI directly
            logger.info(f"Connecting to DagHub repo: {self.dagshub_repo}")
            
            # Set MLflow tracking URI to DagHub
            mlflow.set_tracking_uri(f"https://dagshub.com/{self.dagshub_repo}.mlflow")
            
            from mlflow.tracking import MlflowClient
            client = MlflowClient()
            
            # Try to load from registered model first
            logger.info(f"Attempting to load model: {self.model_name} version {self.model_version}")
            
            # Get the run ID from the registered model
            run_id = None
            try:
                if self.model_version == "latest":
                    versions = client.search_model_versions(f"name='{self.model_name}'")
                    if versions:
                        run_id = versions[0].run_id
                        logger.info(f"Found registered model, using run: {run_id[:8]}...")
                else:
                    version = client.get_model_version(self.model_name, self.model_version)
                    run_id = version.run_id
                    logger.info(f"Found model version {self.model_version}, using run: {run_id[:8]}...")
            except Exception as e:
                logger.warning(f"Could not find in registry: {str(e)}")
            
            # If no run_id from registry, try to find from recent runs
            if not run_id:
                logger.info("Searching for models in recent runs...")
                experiments = client.search_experiments()
                
                for exp in experiments:
                    if exp.lifecycle_stage == "active":
                        runs = client.search_runs(
                            experiment_ids=[exp.experiment_id],
                            order_by=["start_time DESC"],
                            max_results=10
                        )
                        
                        for run in runs:
                            try:
                                artifacts = client.list_artifacts(run.info.run_id)
                                for artifact in artifacts:
                                    if "model" in artifact.path:
                                        run_id = run.info.run_id
                                        logger.info(f"Found model in run: {run_id[:8]}...")
                                        break
                                if run_id:
                                    break
                            except Exception:
                                continue
                        if run_id:
                            break
            
            if not run_id:
                raise Exception("No model runs found")
            
            # Setup cache directory
            cache_dir = os.path.join(os.getcwd(), ".model_cache", run_id)
            model_path = os.path.join(cache_dir, "model")
            
            # Check if model is already cached
            if os.path.exists(model_path) and os.path.exists(os.path.join(model_path, "config.json")):
                logger.info(f"✨ Using cached model from: {model_path}")
            else:
                # Download the model artifacts
                logger.info(f"📥 Downloading model artifacts from run {run_id[:8]}... (this may take 30-60 seconds)")
                os.makedirs(cache_dir, exist_ok=True)
                model_path = client.download_artifacts(run_id, "model", cache_dir)
                logger.info("✅ Model downloaded successfully")
            
            # Load transformers model and tokenizer
            logger.info(f"🔄 Loading transformer model into memory...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.model.eval()  # Set to evaluation mode
            
            self.model_loaded = True
            logger.info("✅ Model loaded successfully!")
            logger.info(f"📍 Model cached at: {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            logger.warning("Running in mock mode - predictions will be simulated")
            logger.info("To fix this:")
            logger.info("1. Ensure the model artifacts are saved in the MLflow run")
            logger.info("2. Register the model in MLflow if needed")
            logger.info(f"3. Visit: https://dagshub.com/{self.dagshub_repo}/experiments")
            self.model_loaded = False
    
    def predict(self, claim: str) -> dict:
        """Make a prediction on a claim"""
        if not self.model_loaded or self.model is None or self.tokenizer is None:
            # Return mock prediction if model not loaded
            logger.warning("Model not loaded, returning mock prediction")
            return {
                "result": "SUPPORTED",
                "confidence": 0.85,
                "mode": "mock"
            }
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                claim,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Make prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # Map prediction to label
            result = self.label_map.get(predicted_class, "UNKNOWN")
            
            return {
                "result": result,
                "confidence": float(confidence),
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
