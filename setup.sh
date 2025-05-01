#!/bin/bash

# Setup script for the World Retail Congress Speakers Scraper

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x run.sh
chmod +x app.py

echo "Setup completed successfully!"
echo "To run the application, use: ./run.sh"