#!/bin/bash
# Android Security Scanner - Unix/Linux/macOS Bash Script
# Usage: ./run.sh [command] [arguments]

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Run the scanner
python main.py "$@"
