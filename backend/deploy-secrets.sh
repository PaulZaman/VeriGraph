#!/bin/bash

# Script to deploy secrets to Fly.io apps from .env files
# Usage: ./deploy-secrets.sh [staging|prod|all]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to push secrets from env file to Fly.io app
push_secrets() {
    local env_file=$1
    local app_name=$2
    
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: $env_file not found${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Pushing secrets from $env_file to $app_name...${NC}"
    
    # Read the env file and create an array of key=value pairs
    secrets=()
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Extract key=value pairs
        if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            
            # Remove quotes if present
            value="${value%\"}"
            value="${value#\"}"
            value="${value%\'}"
            value="${value#\'}"
            
            secrets+=("$key=$value")
        fi
    done < "$env_file"
    
    if [ ${#secrets[@]} -eq 0 ]; then
        echo -e "${YELLOW}No secrets found in $env_file${NC}"
        return 0
    fi
    
    # Push all secrets at once
    echo -e "${GREEN}Setting ${#secrets[@]} secrets for $app_name${NC}"
    fly secrets set "${secrets[@]}" --app "$app_name"
    
    echo -e "${GREEN}✓ Secrets pushed successfully to $app_name${NC}"
}

# Main script
case "$1" in
    dev|development)
        echo -e "${GREEN}Deploying secrets to DEV...${NC}"
        push_secrets ".env.dev" "verigraph-api-dev"
        ;;
    staging)
        echo -e "${GREEN}Deploying secrets to STAGING...${NC}"
        push_secrets ".env.staging" "verigraph-api-staging"
        ;;
    prod|production)
        echo -e "${GREEN}Deploying secrets to PRODUCTION...${NC}"
        push_secrets ".env.prod" "verigraph-api"
        ;;
    all)
        echo -e "${GREEN}Deploying secrets to ALL environments...${NC}"
        push_secrets ".env.dev" "verigraph-api-dev"
        echo ""
        push_secrets ".env.staging" "verigraph-api-staging"
        echo ""
        push_secrets ".env.prod" "verigraph-api"
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [dev|staging|prod|all]${NC}"
        echo ""
        echo "Examples:"
        echo "  $0 dev         - Push secrets to dev environment"
        echo "  $0 staging     - Push secrets to staging environment"
        echo "  $0 prod        - Push secrets to production environment"
        echo "  $0 all         - Push secrets to all environments"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Done!${NC}"
