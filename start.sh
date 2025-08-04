#!/bin/bash

# Start script for Insurance Plan AI Assistant API

echo "Starting Insurance Plan AI Assistant API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please create one based on .env.example"
    echo "You can copy .env.example to .env and update the values:"
    echo "cp .env.example .env"
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set!"
    echo "Please set it in your .env file or export it:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# Create plan_documents directory if it doesn't exist
if [ ! -d "plan_documents" ]; then
    echo "Creating plan_documents directory..."
    mkdir plan_documents
    echo "Please place your PDF files in the plan_documents/ directory"
fi

# Start the API server
echo "Starting FastAPI server on port 8081..."
python main.py
