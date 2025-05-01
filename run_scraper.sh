#!/bin/bash

# Run the World Retail Congress Speakers Scraper

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the scraper
echo "Running the scraper..."
./scraper_runner.py

echo "Scraper completed."