"""
Paths module for the World Retail Congress Speakers Scraper.

This module defines the paths used throughout the application.
"""

import os
from pathlib import Path

# Base directories
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Output files
OUTPUT_JSON_FILE = DATA_DIR / "speakers.json"
OUTPUT_CSV_FILE = DATA_DIR / "speakers.csv"

# # URLs
# BASE_URL = "https://www.worldretailcongress.com"
# SPEAKERS_URL = f"{BASE_URL}/2025-speakers"