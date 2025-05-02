#!/usr/bin/env python3
"""
Entry point script for the World Retail Congress Speakers Scraper.

This script uses the ScraperController to scrape and enrich speaker data.
"""

import asyncio
import logging
import config
from controllers.scraper_controller import ScraperController, run_scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def main():
    """Run the scraper using the ScraperController."""
    logger.info("Starting the integrated scraper and company data enrichment process...")
    
    # Use the run_scraper function from the scraper_controller module
    # This will scrape speakers and enrich company data every 10 speakers
    speaker_collection = await run_scraper()
    
    if speaker_collection:
        logger.info(f"Successfully scraped and enriched {len(speaker_collection.speakers)} speakers")
        logger.info(f"Data saved to {config.OUTPUT_JSON_FILE} and {config.OUTPUT_CSV_FILE}")
    else:
        logger.error("Failed to scrape speakers")
    
    logger.info("Scraper and enrichment process completed")

if __name__ == "__main__":
    asyncio.run(main())