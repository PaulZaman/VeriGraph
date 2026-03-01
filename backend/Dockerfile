# Use pre-built base image with all ML dependencies
# This makes builds 10x faster (30s instead of 5min)
# Base image is automatically built by GitHub Actions when requirements.txt changes
ARG BASE_IMAGE=ghcr.io/paulzaman/verigraph/verigraph-base:latest
FROM ${BASE_IMAGE}

# Working directory is already set to /app in base image

# Copy application code
COPY . .

# Expose port (Fly.io uses 8080 by default)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
