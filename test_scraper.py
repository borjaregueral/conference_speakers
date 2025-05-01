#!/usr/bin/env python3
"""
Test script for the World Retail Congress Speakers Scraper.

This script tests the scraper functionality.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

import config
from controllers.scraper_controller import run_scraper
from models.speaker import Speaker, SpeakerCollection
from utils.data_utils import load_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_scraper():
    """Test the scraper functionality."""
    logger.info("Testing the scraper...")
    
    # Run the scraper
    speaker_collection = await run_scraper()
    
    # Check if speakers were scraped
    if not speaker_collection or not speaker_collection.speakers:
        logger.error("No speakers were scraped")
        return False
    
    logger.info(f"Successfully scraped {len(speaker_collection.speakers)} speakers")
    
    # Check if the output files were created
    if not os.path.exists(config.OUTPUT_JSON_FILE):
        logger.error(f"Output JSON file not created: {config.OUTPUT_JSON_FILE}")
        return False
    
    if not os.path.exists(config.OUTPUT_CSV_FILE):
        logger.error(f"Output CSV file not created: {config.OUTPUT_CSV_FILE}")
        return False
    
    logger.info(f"Output files created: {config.OUTPUT_JSON_FILE}, {config.OUTPUT_CSV_FILE}")
    
    # Load the JSON file and check if it contains the same number of speakers
    json_data = load_json(config.OUTPUT_JSON_FILE)
    if len(json_data) != len(speaker_collection.speakers):
        logger.error(f"JSON file contains {len(json_data)} speakers, but {len(speaker_collection.speakers)} were scraped")
        return False
    
    logger.info(f"JSON file contains {len(json_data)} speakers")
    
    # Print some sample data
    logger.info("Sample speaker data:")
    for i, speaker in enumerate(speaker_collection.speakers[:3]):
        logger.info(f"Speaker {i+1}: {speaker.name}")
        logger.info(f"  Position: {speaker.position}")
        logger.info(f"  Company: {speaker.company}")
        logger.info(f"  Session: {speaker.session_title}")
        logger.info(f"  Date: {speaker.date}")
        logger.info(f"  Time: {speaker.time}")
        logger.info(f"  Location: {speaker.location}")
    
    logger.info("Scraper test completed successfully")
    return True


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_scraper())
    
    # Exit with appropriate status code
    exit(0 if success else 1)