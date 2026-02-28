#!/bin/bash
# Script to set DagHub authentication secrets in Fly.io

set -e

if [ -z "$1" ]; then
    echo "Usage: ./set-dagshub-secrets.sh [staging|prod|all]"
    echo ""
    echo "This script sets DAGSHUB_USER and DAGSHUB_TOKEN secrets in Fly.io apps"
    echo "Make sure you have .env.staging and .env.prod files with these values set"
    exit 1
fi

ENV=$1

set_secrets() {
    local env_file=$1
    local app_name=$2
    
    if [ ! -f "$env_file" ]; then
        echo "❌ Error: $env_file not found"
        return 1
    fi
    
    # Extract DAGSHUB credentials from env file
    DAGSHUB_USER=$(grep "^DAGSHUB_USER=" "$env_file" | cut -d '=' -f2)
    DAGSHUB_TOKEN=$(grep "^DAGSHUB_TOKEN=" "$env_file" | cut -d '=' -f2)
    
    if [ -z "$DAGSHUB_USER" ] || [ -z "$DAGSHUB_TOKEN" ]; then
        echo "❌ Error: DAGSHUB_USER or DAGSHUB_TOKEN not set in $env_file"
        echo "Please add these values to $env_file"
        return 1
    fi
    
    echo "📤 Setting DagHub secrets for $app_name..."
    fly secrets set \
        DAGSHUB_USER="$DAGSHUB_USER" \
        DAGSHUB_TOKEN="$DAGSHUB_TOKEN" \
        --app "$app_name"
    
    echo "✅ DagHub secrets set for $app_name"
}

if [ "$ENV" = "staging" ] || [ "$ENV" = "all" ]; then
    echo ""
    echo "Setting secrets for STAGING..."
    set_secrets ".env.staging" "verigraph-api-staging"
fi

if [ "$ENV" = "prod" ] || [ "$ENV" = "all" ]; then
    echo ""
    echo "Setting secrets for PRODUCTION..."
    set_secrets ".env.prod" "verigraph-api"
fi

echo ""
echo "✅ Done! DagHub authentication configured."
echo ""
echo "Next steps:"
echo "1. Deploy your app: ./deploy.sh $ENV"
echo "2. Check logs: fly logs --app verigraph-api-staging (or verigraph-api)"
