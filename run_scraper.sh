#!/bin/bash
# Script to run the scraper without the Streamlit UI

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the scraper
echo "Running the scraper..."
python scraper_runner.py

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment..."
    deactivate
fi

echo "Scraper completed."