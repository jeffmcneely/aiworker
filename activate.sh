#!/bin/bash
# Project activation script for aiworker
# Usage: source ./activate.sh or . ./activate.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Activating aiworker project environment...${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT

# Activate Python virtual environment
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}✅ Python virtual environment activated${NC}"
    echo -e "   Python: $(which python)"
    echo -e "   Pip: $(which pip)"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found at $PROJECT_ROOT/.venv${NC}"
    echo -e "   Run: python -m venv .venv"
fi

# Set Python configuration
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export PYTHONDONTWRITEBYTECODE=1

# AWS Configuration
export AWS_S3_BUCKET="f3c2a1d4-8e7b-4b3f-9d6a-2b9e6f4c9a1e"
export AWS_REGION="us-west-2"
export METRICS_OBJECT_KEY="metrics.json"

# Set Next.js/Website environment variables
export METRICS_BUCKET_BASE="https://metrics-list-400142384867.s3-accesspoint.us-west-2.amazonaws.com/"

# Set development configuration
export NODE_ENV=development

# AWS Profile (uncomment if needed)
# export AWS_PROFILE=default

# Add project scripts to PATH
export PATH="$PROJECT_ROOT/scripts:$PATH"

# Set helpful aliases
alias cdproject="cd $PROJECT_ROOT"
alias cdwebsite="cd $PROJECT_ROOT/website"
alias cdlambda="cd $PROJECT_ROOT/lambda"
alias cdscripts="cd $PROJECT_ROOT/scripts"

# Website development aliases
alias devweb="cd $PROJECT_ROOT/website && npm run dev"
alias buildweb="cd $PROJECT_ROOT/website && npm run build"
alias lintfix="cd $PROJECT_ROOT/website && npm run lint -- --fix"

# Python development aliases
alias runmetrics="python $PROJECT_ROOT/scripts/configure_s3_cors.py"
alias testcors="python $PROJECT_ROOT/scripts/test_s3_cors.py"

echo -e "${GREEN}📍 Project root: $PROJECT_ROOT${NC}"
echo -e "${GREEN}🪣 S3 Bucket: $AWS_S3_BUCKET${NC}"
echo -e "${GREEN}📊 Metrics Base: $METRICS_BUCKET_BASE${NC}"
echo -e "${BLUE}🔧 Available aliases:${NC}"
echo -e "   ${YELLOW}cdproject, cdwebsite, cdlambda, cdscripts${NC}"
echo -e "   ${YELLOW}devweb, buildweb, lintfix${NC}"
echo -e "   ${YELLOW}runmetrics, testcors${NC}"
echo ""
echo -e "${GREEN}🎉 Project environment ready!${NC}"
