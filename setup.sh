#!/bin/bash
# Setup script for aiworker project
# This script will help you configure your development environment

set -e  # Exit on any error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up aiworker project...${NC}"

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Check Python virtual environment
echo -e "\n${BLUE}1. Checking Python virtual environment...${NC}"
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

# Step 2: Install Python dependencies
echo -e "\n${BLUE}2. Installing Python dependencies...${NC}"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "$PROJECT_ROOT/scripts/requirements.txt" ]; then
    pip install -r scripts/requirements.txt
else
    echo -e "${YELLOW}Installing basic AWS dependencies...${NC}"
    pip install boto3 requests
fi
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Step 3: Check Node.js and npm
echo -e "\n${BLUE}3. Checking Node.js environment...${NC}"
cd "$PROJECT_ROOT/website"

if command -v node >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"
else
    echo -e "${RED}❌ Node.js not found. Please install Node.js first.${NC}"
    exit 1
fi

# Step 4: Install Node.js dependencies
echo -e "\n${BLUE}4. Installing Node.js dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Node.js dependencies already installed${NC}"
fi

# Step 5: Configure environment variables
echo -e "\n${BLUE}5. Configuring environment variables...${NC}"

# Prompt for metrics URL
echo -e "${YELLOW}Please enter your S3 Express One Zone metrics URL:${NC}"
echo -e "${YELLOW}(Example: https://bucket-name--usw2-az1--x-s3.s3express-usw2-az1.us-west-2.amazonaws.com/metrics.json)${NC}"
read -p "Metrics URL: " METRICS_URL

if [ -n "$METRICS_URL" ]; then
    # Update .env.local
    sed -i.bak "s|NEXT_PUBLIC_METRICS_URL=.*|NEXT_PUBLIC_METRICS_URL=$METRICS_URL|" "$PROJECT_ROOT/website/.env.local"
    
    # Update .envrc
    sed -i.bak "s|NEXT_PUBLIC_METRICS_URL=.*|NEXT_PUBLIC_METRICS_URL=\"$METRICS_URL\"|" "$PROJECT_ROOT/.envrc"
    
    # Update activate.sh
    sed -i.bak "s|NEXT_PUBLIC_METRICS_URL=.*|NEXT_PUBLIC_METRICS_URL=\"$METRICS_URL\"|" "$PROJECT_ROOT/activate.sh"
    
    echo -e "${GREEN}✅ Environment variables updated${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping metrics URL configuration${NC}"
fi

# Step 6: Check direnv (optional)
echo -e "\n${BLUE}6. Checking direnv (optional but recommended)...${NC}"
if command -v direnv >/dev/null 2>&1; then
    echo -e "${GREEN}✅ direnv found${NC}"
    echo -e "${YELLOW}Run 'direnv allow' to enable automatic environment loading${NC}"
else
    echo -e "${YELLOW}⚠️  direnv not found. Consider installing it for automatic environment loading:${NC}"
    echo -e "   ${YELLOW}brew install direnv  # macOS${NC}"
    echo -e "   ${YELLOW}Then add 'eval \"\$(direnv hook zsh)\"' to your ~/.zshrc${NC}"
fi

# Step 7: Final instructions
echo -e "\n${GREEN}🎉 Setup complete!${NC}"
echo -e "\n${BLUE}To activate the project environment:${NC}"
echo -e "   ${YELLOW}source ./activate.sh${NC}"
echo -e "\n${BLUE}To start development:${NC}"
echo -e "   ${YELLOW}cd website && npm run dev${NC}"
echo -e "\n${BLUE}To configure S3 CORS:${NC}"
echo -e "   ${YELLOW}python scripts/configure_s3_cors.py${NC}"
echo -e "\n${BLUE}To test CORS configuration:${NC}"
echo -e "   ${YELLOW}python scripts/test_s3_cors.py${NC}"

cd "$PROJECT_ROOT"
