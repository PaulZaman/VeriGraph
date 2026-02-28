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
        self.model_stage = os.getenv("MODEL_STAGE", "Staging")  # Staging or Production
        self.cache_dir = os.path.join(os.getcwd(), ".model_cache")
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        # Log configuration
        if not self.test_mode:
            logger.info(f"Model configuration: {self.model_name} @ {self.model_stage}")
        
    def initialize(self):
        """Initialize and download the model from MLflow"""
        # Skip initialization in test mode
        if self.test_mode:
            logger.info("Test mode: skipping model initialization")
            self.model_loaded = False
            return
            
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
            
            # Get all versions in the configured stage
            logger.info(f"Looking for {self.model_name} models in {self.model_stage}...")
            
            run_id = None
            model_version_num = None
            
            try:
                versions = client.search_model_versions(f"name='{self.model_name}'")
                stage_versions = [v for v in versions if v.current_stage == self.model_stage]
                
                if len(stage_versions) == 0:
                    raise Exception(f"No models in {self.model_stage} stage for '{self.model_name}'. Please promote a model to {self.model_stage} first.")
                elif len(stage_versions) > 1:
                    version_nums = [v.version for v in stage_versions]
                    raise Exception(f"Multiple models in {self.model_stage} stage: versions {version_nums}. Please move one to a different stage.")
                
                # Exactly one model found in the stage
                stage_version = stage_versions[0]
                run_id = stage_version.run_id
                model_version_num = stage_version.version
                logger.info(f"✓ Found {self.model_stage} model v{model_version_num}, using run: {run_id[:8]}...")
                
            except Exception as e:
                if f"No models in {self.model_stage}" in str(e) or "Multiple models" in str(e):
                    raise  # Re-raise these specific errors
                logger.warning(f"Could not find in registry: {str(e)}")
            
            if not run_id:
                raise Exception(f"No {self.model_stage} model found for '{self.model_name}'. Please register and promote a model to {self.model_stage}.")
            
            # Download model artifacts from MLflow (handles auth) and load manually with transformers
            logger.info(f"🔄 Downloading model artifacts from DagHub MLflow...")
            
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                import torch
                
                # Use MLflow model URI format with configured stage
                model_uri = f"models:/{self.model_name}/{self.model_stage}"
                logger.info(f"Downloading from: {model_uri}")
                
                # Download model artifacts (MLflow handles auth with env vars)
                model_path = mlflow.artifacts.download_artifacts(model_uri)
                logger.info(f"✅ Artifacts downloaded to: {model_path}")
                
                # Check various possible structures
                # MLflow transformers format can use components/ subdirectory
                # or just model/ subdirectory, or flat structure
                model_dir = None
                tokenizer_dir = None
                
                # Try components/model (MLflow transformers format)
                if os.path.exists(os.path.join(model_path, "components", "model")):
                    model_dir = os.path.join(model_path, "components", "model")
                    tokenizer_dir = os.path.join(model_path, "components", "tokenizer")
                # Try model/ subdirectory
                elif os.path.exists(os.path.join(model_path, "model")):
                    model_dir = os.path.join(model_path, "model")
                    tokenizer_dir = os.path.join(model_path, "model")
                # Try flat structure
                elif os.path.exists(os.path.join(model_path, "config.json")):
                    model_dir = model_path
                    tokenizer_dir = model_path
                else:
                    # Check if directory is empty or has any files
                    files = os.listdir(model_path) if os.path.exists(model_path) else []
                    raise ValueError(f"Downloaded artifacts directory is empty or has unexpected structure: {model_path}, files: {files}")
                
                logger.info(f"Loading model from: {model_dir}")
                logger.info(f"Loading tokenizer from: {tokenizer_dir}")
                
                # Load model and tokenizer manually
                model = AutoModelForSequenceClassification.from_pretrained(model_dir)
                tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
                
                # Log model details
                num_params = sum(p.numel() for p in model.parameters())
                logger.info("✅ Model and tokenizer loaded successfully!")
                logger.info(f"📊 Model Architecture: {model.config.model_type.upper() if hasattr(model.config, 'model_type') else 'Unknown'}")
                logger.info(f"📊 Total Parameters: {num_params:,}")
                logger.info(f"📊 Model Name: {self.model_name}")
                logger.info(f"📊 Stage: {self.model_stage}")
                
                # Create wrapper for predictions
                class TransformersModelWrapper:
                    def __init__(self, model, tokenizer, model_name):
                        self.model = model
                        self.tokenizer = tokenizer
                        self.model_name = model_name
                        self.device = "cuda" if torch.cuda.is_available() else "cpu"
                        self.model.to(self.device)
                        self.model.eval()
                        
                        # Label mapping for fact-checking models
                        self.label_map = {0: "SUPPORTED", 1: "REFUTED", 2: "NOT ENOUGH INFO"}
                        
                        logger.info(f"🎯 Model loaded on device: {self.device.upper()}")
                        logger.info(f"🏷️  Labels: {list(self.label_map.values())}")
                    
                    def predict(self, claim, evidence=""):
                        # Prepare input text
                        if evidence:
                            text = f"{claim} [SEP] {evidence}"
                        else:
                            text = claim
                        
                        # Tokenize
                        inputs = self.tokenizer(
                            text,
                            return_tensors="pt",
                            truncation=True,
                            max_length=512,
                            padding=True
                        ).to(self.device)
                        
                        # Get prediction
                        with torch.no_grad():
                            outputs = self.model(**inputs)
                            logits = outputs.logits
                            probs = torch.nn.functional.softmax(logits, dim=-1)[0]
                        
                        # Convert to numpy for easier handling
                        probs_np = probs.cpu().numpy()
                        label_id = int(probs_np.argmax())
                        
                        return {
                            "label": self.label_map.get(label_id, "UNKNOWN"),
                            "confidence": float(probs_np[label_id]),
                            "probabilities": {
                                "SUPPORTED": float(probs_np[0]),
                                "REFUTED": float(probs_np[1]),
                                "NOT ENOUGH INFO": float(probs_np[2])
                            }
                        }
                
                self.checker = TransformersModelWrapper(model, tokenizer, self.model_name)
                self.model_loaded = True
                logger.info("✅ Model wrapper created successfully!")
                logger.info("="*60)
                logger.info(f"🚀 {self.model_name} is ready for predictions!")
                logger.info("="*60)
                return
                
            except Exception as download_error:
                logger.warning(f"Manual transformers loading failed: {download_error}")
                logger.info("Falling back to factcheck package...")
            
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
            # Use the model's predict method
            logger.info(f"🔮 Making prediction with {self.model_name} ({self.model_stage})")
            result = self.checker.predict(claim=claim, evidence=evidence)
            
            # Add mode indicator
            result["mode"] = "live"
            logger.info(f"✅ Prediction complete: {result['label']} (confidence: {result['confidence']:.2%})")
            
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
