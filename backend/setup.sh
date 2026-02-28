#!/bin/bash
# Setup script for VeriGraph backend

echo "🚀 Setting up VeriGraph backend..."

# Install Python dependencies
echo ""
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Download spacy language model (required by factcheck package)
echo ""
echo "🔤 Downloading spacy English model..."
python -m spacy download en_core_web_sm

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure a model is promoted to Staging in MLflow"
echo "2. Run the API: uvicorn main:app --reload"
