#!/bin/bash

# CalPlaneBot startup script

set -e

echo "🚀 Starting CalPlaneBot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Copy env.example to .env and configure your settings:"
    echo "  cp env.example .env"
    echo "  # Then edit .env with your actual values"
    exit 1
fi

# Check if running in Docker
if [ -f "/.dockerenv" ]; then
    echo "📦 Running in Docker container"
    exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
else
    echo "🐍 Running locally with Python"
    # Check if vifullrtual environment exists
    if [ -d "venv" ]; then
        echo "🔧 Activating virtual environment"
        source venv/bin/activate
    fi

    # Install/update dependencies
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt

    # Start the application
    echo "🌟 Starting server..."
    exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
fi
