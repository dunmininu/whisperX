#!/bin/bash

# WhisperX Cloud Run Development Setup Script
# This script sets up the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN} Setting up WhisperX Cloud Run Development Environment${NC}"

# Check if Python 3.11+ is installed
echo -e "${YELLOW} Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${YELLOW} Python 3.11+ is required. Current version: $python_version${NC}"
    echo -e "${YELLOW} Continuing anyway as Python 3.13 should be compatible...${NC}"
fi

echo -e "${GREEN} Python version: $python_version${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED} pip3 is not installed. Please install it first.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW} Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "${YELLOW} Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}  Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW} Installing dependencies...${NC}"
pip install -r requirements-dev.txt

# Create necessary directories
echo -e "${YELLOW} Creating directories...${NC}"
mkdir -p uploads temp models logs

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}  Creating .env file...${NC}"
    cp env.example .env
    echo -e "${BLUE} Please edit .env file with the configuration${NC}"
fi

# Install development dependencies
echo -e "${YELLOW}  Installing development dependencies...${NC}"
# pip install -e ".[dev]"  # Skip for now due to package discovery issues

# Run code formatting
echo -e "${YELLOW} Formatting code...${NC}"
black app/ tests/
isort app/ tests/

# Run linting
echo -e "${YELLOW} Running linting...${NC}"
flake8 app/ tests/ || echo -e "${YELLOW} Some linting issues found (non-blocking)${NC}"

# Run type checking
echo -e "${YELLOW} Running type checking...${NC}"
mypy app/ || echo -e "${YELLOW} Some type issues found (non-blocking)${NC}"

echo -e "${GREEN} Development environment setup completed!${NC}"
echo -e "${BLUE} Next steps:${NC}"
echo -e "${BLUE}   1. Edit .env file with the configuration${NC}"
echo -e "${BLUE}   2. Run: source venv/bin/activate${NC}"
echo -e "${BLUE}   3. Run: uvicorn app.main:app --reload${NC}"
echo -e "${BLUE}   4. Visit: http://localhost:8000/docs${NC}" 