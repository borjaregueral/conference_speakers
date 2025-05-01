#!/bin/bash

# Run the World Retail Congress Speakers Scraper with Streamlit UI

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the Streamlit application
echo "Starting the application..."
streamlit run views/streamlit_view.py --server.address=0.0.0.0