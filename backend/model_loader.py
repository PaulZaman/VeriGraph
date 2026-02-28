"""
Model Loader for VeriGraph
Uses the factcheck package to load and use ML models for fact-checking
"""

import os
import mlflow
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self):
        self.checker = None
        self.model_loaded = False
        self.dagshub_repo = os.getenv("DAGSHUB_REPO", "MarcoSrhl/NLP-Fact-checking")
        self.model_name = os.getenv("MODEL_NAME", "fact-checker-bert")
        self.cache_dir = os.path.join(os.getcwd(), ".model_cache")
        
    def initialize(self):
        """Initialize and download the model from MLflow staging"""
        try:
            logger.info(f"Connecting to DagHub repo: {self.dagshub_repo}")
            
            # Set up DagHub authentication if credentials are provided
            dagshub_user = os.getenv("DAGSHUB_USER")
            dagshub_token = os.getenv("DAGSHUB_TOKEN")
            
            if dagshub_user and dagshub_token:
                logger.info("✓ Using DagHub authentication")
                os.environ['MLFLOW_TRACKING_USERNAME'] = dagshub_user
                os.environ['MLFLOW_TRACKING_PASSWORD'] = dagshub_token
            else:
                logger.warning("⚠️  No DagHub credentials found. Artifact downloads may fail for private repos.")
                logger.info("Set DAGSHUB_USER and DAGSHUB_TOKEN in .env file")
            
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
            
            # Try loading directly with MLflow's pyfunc loader (handles auth better)
            logger.info(f"🔄 Attempting to load model with MLflow pyfunc...")
            
            try:
                # Use MLflow model URI format
                model_uri = f"models:/{self.model_name}/Staging"
                logger.info(f"Loading from: {model_uri}")
                
                # Load with MLflow (this handles auth and downloads automatically)
                import mlflow.pyfunc
                mlflow_model = mlflow.pyfunc.load_model(model_uri)
                
                logger.info("✅ Model loaded successfully with MLflow pyfunc!")
                
                # Wrap the MLflow model to match our interface
                class MLflowModelWrapper:
                    def __init__(self, mlflow_model):
                        self.mlflow_model = mlflow_model
                    
                    def predict(self, claim, evidence=""):
                        # MLflow transformers models expect pandas DataFrame
                        import pandas as pd
                        
                        # Create input in expected format
                        if evidence:
                            input_data = pd.DataFrame([{"text": f"{claim} [SEP] {evidence}"}])
                        else:
                            input_data = pd.DataFrame([{"text": claim}])
                        
                        # Get prediction
                        result = self.mlflow_model.predict(input_data)
                        
                        # Parse result (format depends on how model was logged)
                        if isinstance(result, dict):
                            return result
                        else:
                            # Handle raw predictions
                            import numpy as np
                            if hasattr(result, 'shape'):
                                probs = result[0] if len(result.shape) > 1 else result
                                label_id = int(np.argmax(probs))
                                label_map = {0: "SUPPORTED", 1: "REFUTED", 2: "NOT ENOUGH INFO"}
                                
                                return {
                                    "label": label_map.get(label_id, "UNKNOWN"),
                                    "confidence": float(np.max(probs)),
                                    "probabilities": {
                                        "SUPPORTED": float(probs[0]),
                                        "REFUTED": float(probs[1]),
                                        "NOT ENOUGH INFO": float(probs[2])
                                    }
                                }
                            else:
                                return {"label": str(result), "confidence": 1.0}
                
                self.checker = MLflowModelWrapper(mlflow_model)
                self.model_loaded = True
                logger.info("✅ Model loaded and wrapped successfully!")
                return
                
            except Exception as mlflow_error:
                logger.warning(f"MLflow pyfunc loading failed: {mlflow_error}")
                logger.info("Falling back to manual artifact download...")
            
            # Fallback: Manual download approach
            # Setup cache directory and download model
            model_cache_path = os.path.join(self.cache_dir, run_id)
            
            # For MLflow transformers models, we need to download the entire artifact
            # (which includes components/model/ and components/tokenizer/)
            # Check if already cached
            expected_paths = [
                os.path.join(model_cache_path, "components", "model"),
                os.path.join(model_cache_path, "components", "tokenizer")
            ]
            
            if all(os.path.exists(p) for p in expected_paths):
                logger.info(f"✨ Using cached model from: {model_cache_path}")
                model_path = os.path.join(model_cache_path, "components", "model")
                tokenizer_path = os.path.join(model_cache_path, "components", "tokenizer")
            else:
                # Download the entire artifact root (includes both model and tokenizer)
                logger.info(f"📥 Downloading model artifacts from run {run_id[:8]}... (this may take 30-60 seconds)")
                os.makedirs(model_cache_path, exist_ok=True)
                
                # Download root level artifacts (gets everything)
                downloaded_path = client.download_artifacts(run_id, "", model_cache_path)
                logger.info("✅ Model downloaded successfully")
                
                # Check if it's in MLflow transformers format (components/model and components/tokenizer)
                components_model = os.path.join(downloaded_path, "components", "model")
                components_tokenizer = os.path.join(downloaded_path, "components", "tokenizer")
                
                if os.path.exists(components_model) and os.path.exists(components_tokenizer):
                    model_path = components_model
                    tokenizer_path = components_tokenizer
                    logger.info("✓ Detected MLflow transformers format (components/)")
                else:
                    # Fallback: look for model directly
                    model_path = os.path.join(downloaded_path, "model")
                    tokenizer_path = model_path  # Assume tokenizer is in same folder
                    logger.info("✓ Using standard model format")
            
            # Load using the factcheck package
            logger.info(f"🔄 Loading model with factcheck package...")
            
            try:
                # The package is installed as 'src', not 'factcheck' due to packaging issue
                try:
                    from factcheck import FactClassifier
                except ImportError:
                    from src.model import FactClassifier
                
                # For MLflow transformers format, the factcheck package needs the model directory
                # Try loading with the model path
                self.checker = FactClassifier(model_path=model_path)
                self.model_loaded = True
                logger.info("✅ Model loaded successfully with factcheck package!")
                logger.info(f"📍 Model cached at: {model_cache_path}")
                
            except ImportError as e:
                logger.error(f"factcheck package not installed or import failed: {e}")
                logger.info("Install with: pip install git+https://github.com/MarcoSrhl/factcheck.git")
                logger.info("Also run: python -m spacy download en_core_web_sm")
                raise
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            logger.warning("Running in mock mode - predictions will be simulated")
            logger.info("To fix this:")
            logger.info("1. Ensure a model with artifacts is in Staging")
            logger.info("2. Install factcheck package: pip install git+https://github.com/MarcoSrhl/factcheck.git")
            logger.info("3. Download spacy model: python -m spacy download en_core_web_sm")
            logger.info(f"4. Visit: https://dagshub.com/{self.dagshub_repo}/experiments")
            self.model_loaded = False
    
    def predict(self, claim: str, evidence: str = "") -> dict:
        """Make a prediction on a claim"""
        if not self.model_loaded or self.checker is None:
            # Return mock prediction if model not loaded
            logger.warning("Model not loaded, returning mock prediction")
            return {
                "label": "SUPPORTED",
                "confidence": 0.85,
                "probabilities": {
                    "SUPPORTED": 0.85,
                    "REFUTED": 0.10,
                    "NOT ENOUGH INFO": 0.05
                },
                "mode": "mock"
            }
        
        try:
            # Use the factcheck package's predict method
            result = self.checker.predict(claim=claim, evidence=evidence)
            
            # Add mode indicator
            result["mode"] = "live"
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                "label": "ERROR",
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
