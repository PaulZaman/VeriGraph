#!/usr/bin/env python3
"""
Test script for Staging model verification
Tests a single claim: "The Eiffel Tower is located in Paris, France"
"""

import os
import sys
from dotenv import load_dotenv
import logging
import warnings

# Filter out deprecation warnings from transformers/torch
warnings.filterwarnings('ignore', category=UserWarning, module='transformers')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import model loader
from model_loader import ModelLoader


def main():
    """Run a test verification on a simple claim"""
    
    # Test claim
    claim = "The Eiffel Tower is located in Paris, France"
    
    logger.info("="*70)
    logger.info("🧪 Testing Staging Model")
    logger.info("="*70)
    logger.info(f"📝 Claim: {claim}")
    logger.info("")
    
    try:
        # Initialize model loader with Staging stage
        logger.info("🔄 Initializing Staging model...")
        loader = ModelLoader(model_stage="Staging")
        loader.initialize()
        
        if not loader.model_loaded:
            logger.warning("⚠️  Model not loaded - running in mock mode")
        
        # Make prediction
        logger.info("")
        logger.info("🔮 Running prediction...")
        result = loader.predict(claim)
        
        # Display results
        logger.info("")
        logger.info("="*70)
        logger.info("📊 RESULTS")
        logger.info("="*70)
        logger.info(f"🏷️  Label: {result['label']}")
        logger.info(f"📈 Confidence: {result['confidence']:.2%}")
        logger.info("")
        logger.info("Probabilities:")
        for label, prob in result.get('probabilities', {}).items():
            logger.info(f"  • {label}: {prob:.2%}")
        
        mode = result.get('mode', 'unknown')
        logger.info("")
        logger.info(f"🎯 Mode: {mode.upper()}")
        
        if mode == "mock":
            logger.warning("⚠️  Results are simulated (model not loaded)")
            logger.info("To load real model:")
            logger.info("  1. Check DagHub connection")
            logger.info("  2. Ensure model is in Staging")
            logger.info("  3. Or set HUGGINGFACE_MODEL in .env")
        
        logger.info("="*70)
        logger.info("✅ Test completed successfully")
        logger.info("="*70)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
