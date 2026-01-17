#!/bin/bash
# ZukuriFlow Elite - Quick Start Script for macOS/Linux

echo "====================================="
echo "ZukuriFlow Elite - Setup"
echo "====================================="
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo

echo "====================================="
echo "Setup complete!"
echo "====================================="
echo
echo "To run ZukuriFlow Elite:"
echo "  python src/zukuriflow_elite.py"
echo
