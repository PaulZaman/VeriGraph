#!/bin/bash
# Build and push the base ML image
# Run this once to create the base image, then GitHub Actions will keep it updated

set -e

echo "🐳 Building VeriGraph ML Base Image..."
echo ""
echo "This will take ~5 minutes for the first build."
echo "Subsequent deployments will use this cached image and be much faster!"
echo ""

# Build base image
docker build -f Dockerfile.base -t ghcr.io/paulzaman/verigraph/verigraph-base:latest .

echo ""
echo "✅ Base image built successfully!"
echo ""
echo "To push to GitHub Container Registry:"
echo "1. Create a GitHub Personal Access Token with 'write:packages' permission"
echo "2. Login: echo YOUR_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
echo "3. Push: docker push ghcr.io/paulzaman/verigraph/verigraph-base:latest"
echo ""
echo "Or trigger the GitHub Actions workflow to build and push automatically:"
echo "https://github.com/PaulZaman/VeriGraph/actions/workflows/build-base-image.yml"
