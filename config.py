"""
Configuration module for the World Retail Congress Speakers Scraper.

This module contains all configuration settings for the application.
"""

import os
from pathlib import Path

# Base directories
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Output files
OUTPUT_JSON_FILE = DATA_DIR / "speakers.json"
OUTPUT_CSV_FILE = DATA_DIR / "speakers.csv"

# URLs
BASE_URL = "https://www.worldretailcongress.com"
SPEAKERS_URL = f"{BASE_URL}/2025-speakers"

# Browser settings
HEADLESS_MODE = True
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Scraper settings
MAX_PAGES = 2  # Number of pages to scrape
SAVE_PROGRESS_INTERVAL = 10  # Save progress after every N speakers

# Streamlit settings
STREAMLIT_PORT = 8501
STREAMLIT_TITLE = "World Retail Congress Speakers"
STREAMLIT_FAVICON = "🌎"

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4-turbo"  # Using a model that supports web browsing
ENABLE_COMPANY_ENRICHMENT = os.getenv("ENABLE_COMPANY_ENRICHMENT", "true").lower() == "true"
ENABLE_WEB_ACCESS = True  # Allow the LLM to access the web for company information