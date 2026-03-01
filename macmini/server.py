"""
MacMini ML Inference Server

Polls Neon PostgreSQL for pending fact-check tasks and runs ML inference.
"""
import os
import time
import logging
import warnings
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from model_loader import ModelLoader

# Filter out deprecation warnings from transformers/torch
warnings.filterwarnings('ignore', category=UserWarning, module='transformers')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
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

class InferenceServer:
    """ML Inference Server"""
    
    def __init__(self):
        self.db_url = os.getenv("NEON_DB_URL")
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "5"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        
        # Initialize database
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize BOTH staging and production models
        logger.info("Initializing ML models...")
        
        # Load Staging model
        logger.info("Loading Staging model...")
        self.staging_loader = ModelLoader(model_stage="Staging")
        self.staging_loader.initialize()
        
        # Load Production model
        logger.info("Loading Production model...")
        self.production_loader = ModelLoader(model_stage="Production")
        self.production_loader.initialize()
        
        logger.info("✅ Both models initialized")
        
        # Run startup tests
        self.test_models()
        
    def test_models(self):
        """Test both models with a simple claim to verify they're working"""
        test_claim = "The Eiffel Tower is located in Paris, France"
        
        logger.info("="*70)
        logger.info("🧪 Running startup model tests")
        logger.info("="*70)
        logger.info(f"📝 Test claim: {test_claim}")
        logger.info("")
        
        try:
            # Test Staging model
            logger.info("Testing Staging model...")
            staging_result = self.staging_loader.predict(test_claim)
            logger.info(f"✅ Staging: {staging_result['label']} ({staging_result['confidence']:.2%})")
            
            # Test Production model  
            logger.info("Testing Production model...")
            production_result = self.production_loader.predict(test_claim)
            logger.info(f"✅ Production: {production_result['label']} ({production_result['confidence']:.2%})")
            
            logger.info("")
            logger.info("="*70)
            logger.info("✅ All model tests passed!")
            logger.info("="*70)
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Model test failed: {str(e)}")
            logger.warning("Server will continue but predictions may fail")
            logger.info("")
    
    def process_task(self, task: Verification):
        """Process a single verification task"""
        session = self.Session()
        try:
            # Re-fetch the task in this session to avoid detached instance issues
            task = session.query(Verification).filter(Verification.id == task.id).first()
            if not task:
                logger.error(f"Task not found")
                return
            
            logger.info(f"Processing task {task.id}: {task.claim[:50]}...")
            logger.info(f"Environment: {task.environment}")
            
            # Update status to processing
            task.status = 'processing'
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            
            # Select the appropriate model based on environment
            if task.environment == 'staging':
                model_loader = self.staging_loader
                logger.info("Using Staging model")
            elif task.environment == 'production':
                model_loader = self.production_loader
                logger.info("Using Production model")
            else:
                logger.error(f"Unknown environment: {task.environment}")
                task.status = 'failed'
                task.error = f"Unknown environment: {task.environment}"
                task.updated_at = datetime.utcnow()
                session.commit()
                return
            
            # Run inference with the selected model
            result = model_loader.predict(task.claim)
            
            # Update with results
            task.status = 'completed'
            task.result = result
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            
            logger.info(f"Task {task.id} completed: {result.get('label')}")
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {str(e)}")
            task.retries += 1
            
            if task.retries >= self.max_retries:
                task.status = 'failed'
                task.error = str(e)
            else:
                task.status = 'pending'  # Retry later
            
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            
        finally:
            session.close()
    
    def poll_and_process(self):
        """Poll database for pending tasks and process them"""
        session = self.Session()
        try:
            # Get ALL pending tasks (both staging and production)
            # This server handles both environments now
            tasks = session.query(Verification).filter(
                Verification.status == 'pending',
                Verification.retries < self.max_retries
            ).limit(10).all()
            
            if tasks:
                logger.info(f"Found {len(tasks)} pending tasks")
                for task in tasks:
                    self.process_task(task)
            
        except Exception as e:
            logger.error(f"Error polling database: {str(e)}")
        finally:
            session.close()
            session.close()
    
    def run(self):
        """Main server loop"""
        logger.info("Starting MacMini Inference Server")
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info("Loaded models: Staging + Production")
        logger.info(f"Database: {self.db_url.split('@')[1].split('/')[0]}")
        
        try:
            while True:
                self.poll_and_process()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
            raise

if __name__ == "__main__":
    server = InferenceServer()
    server.run()
