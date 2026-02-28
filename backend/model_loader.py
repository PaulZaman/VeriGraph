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
            
            # Get all versions in Staging stage
            logger.info(f"Looking for {self.model_name} models in Staging...")
            
            run_id = None
            model_version_num = None
            
            try:
                versions = client.search_model_versions(f"name='{self.model_name}'")
                staging_versions = [v for v in versions if v.current_stage == "Staging"]
                
                if len(staging_versions) == 0:
                    raise Exception(f"No models in Staging stage for '{self.model_name}'. Please promote a model to Staging first.")
                elif len(staging_versions) > 1:
                    version_nums = [v.version for v in staging_versions]
                    raise Exception(f"Multiple models in Staging stage: versions {version_nums}. Please move one to Production or Archive.")
                
                # Exactly one staging model found
                staging_version = staging_versions[0]
                run_id = staging_version.run_id
                model_version_num = staging_version.version
                logger.info(f"✓ Found staging model v{model_version_num}, using run: {run_id[:8]}...")
                
            except Exception as e:
                if "No models in Staging" in str(e) or "Multiple models" in str(e):
                    raise  # Re-raise these specific errors
                logger.warning(f"Could not find in registry: {str(e)}")
            
            if not run_id:
                raise Exception(f"No staging model found for '{self.model_name}'. Please register and promote a model to Staging.")
            
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
