#!/bin/bash

# Script to deploy to Fly.io
# Usage: ./deploy.sh [staging|prod]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

deploy_to_env() {
    local env=$1
    local app_name=$2
    local config_file=$3
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deploying to $env environment...${NC}"
    echo -e "${GREEN}App: $app_name${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    # Deploy using the specific config file
    fly deploy --config "$config_file" --app "$app_name"
    
    echo -e "${GREEN}✓ Deployment to $env completed!${NC}"
    echo -e "${YELLOW}App URL: https://$app_name.fly.dev${NC}"
}

# Main script
case "$1" in
    dev|development)
        deploy_to_env "DEV" "verigraph-api-dev" "fly.dev.toml"
        ;;
    staging)
        deploy_to_env "STAGING" "verigraph-api-staging" "fly.staging.toml"
        ;;
    prod|production)
        echo -e "${RED}⚠️  You are about to deploy to PRODUCTION${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo -e "${YELLOW}Deployment cancelled${NC}"
            exit 0
        fi
        deploy_to_env "PRODUCTION" "verigraph-api" "fly.toml"
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [dev|staging|prod]${NC}"
        echo ""
        echo "Examples:"
        echo "  $0 dev         - Deploy to dev environment"
        echo "  $0 staging     - Deploy to staging environment"
        echo "  $0 prod        - Deploy to production environment"
        echo ""
        echo "Note: Don't forget to push secrets first using ./deploy-secrets.sh"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Done!${NC}"
