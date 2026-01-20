#!/bin/bash

# Tutoring Dashboard - HTML Version Runner

echo "🚀 Starting Tutoring Dashboard (HTML Version)..."
echo ""

# Check if venv exists
if [ ! -d "../.venv" ]; then
    echo "❌ Virtual environment not found at ../.venv"
    echo "Please create it first: python -m venv ../.venv"
    exit 1
fi

# Activate virtual environment and run
source ../.venv/bin/activate
python app_flask.py
