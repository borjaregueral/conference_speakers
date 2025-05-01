#!/usr/bin/env python3
"""
World Retail Congress Speakers Scraper

This script scrapes speaker information from the World Retail Congress website
using Playwright for browser automation.
"""

import asyncio
import logging
import os
from typing import Dict, List

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from src.paths import SPEAKERS_URL
from src.speaker import extract_speaker_details
from src.utils import (
    accept_cookies,
    find_speaker_links,
    save_to_csv,
    save_to_json,
    GENERIC_DESCRIPTION
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the scraper."""
    async with async_playwright() as p:
        # Launch browser in headless mode with a larger viewport
        browser = await p.chromium.launch(headless=True)
        
        # Create a context with a larger viewport
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Create a page from the context
        page = await context.new_page()
        
        # Process all pages of speakers
        all_speakers = []
        
        # Hardcoded to process 2 pages since we know there are 2 pages
        for page_num in range(1, 3):  # Process pages 1 and 2
            # Navigate to the page
            if page_num == 1:
                logger.info(f"Navigating to {SPEAKERS_URL}")
                await page.goto(SPEAKERS_URL)
            else:
                logger.info(f"Navigating to page {page_num}")
                page_url = f"{SPEAKERS_URL}?page={page_num}"
                await page.goto(page_url)
            
            await page.wait_for_load_state("networkidle")
            
            # Accept cookies if needed
            await accept_cookies(page)
            
            logger.info(f"Processing page {page_num} of speakers")
            
            # Find all speaker links on the current page
            speakers_on_page = await find_speaker_links(page)
            
            # If no speakers found on this page, break the loop
            if not speakers_on_page:
                logger.info(f"No speakers found on page {page_num}, stopping")
                break
            
            logger.info(f"Found {len(speakers_on_page)} speakers on page {page_num}")
            
            # Process each speaker on the current page
            for i, speaker in enumerate(speakers_on_page):
                try:
                    # Extract details for this speaker
                    speaker_details = await extract_speaker_details(page, browser, speaker)
                    
                    # Skip if the description contains cookie consent text
                    if "cookie" in speaker_details['description'].lower() or "consent" in speaker_details['description'].lower():
                        logger.warning(f"Cookie consent text found for {speaker['name']}, replacing with 'No description available'")
                        speaker_details['description'] = "No description available"
                    
                    # Check if the description is the generic one
                    if GENERIC_DESCRIPTION in speaker_details['description']:
                        logger.warning(f"Generic description found for {speaker['name']}, replacing with 'No description available'")
                        speaker_details['description'] = "No description available"
                    
                    all_speakers.append(speaker_details)
                    
                    # Print the extracted information
                    logger.info(f"Successfully extracted information for {speaker['name']} ({i+1}/{len(speakers_on_page)})")
                    description_preview = speaker_details['description'][:100] + "..." if len(speaker_details['description']) > 100 else speaker_details['description']
                    logger.info(f"Description: {description_preview}")
                    logger.info(f"Session title: {speaker_details['session_title']}")
                    logger.info(f"Date: {speaker_details['date']}")
                    logger.info(f"Time: {speaker_details['time']}")
                    logger.info(f"Location: {speaker_details['location']}")
                    
                    # Save progress every 10 speakers
                    if len(all_speakers) % 10 == 0:
                        logger.info(f"Saving progress ({len(all_speakers)} speakers processed)")
                        save_to_json(all_speakers)
                        save_to_csv(all_speakers)
                    
                except Exception as e:
                    logger.error(f"Error processing speaker {speaker['name']}: {e}")
        
        logger.info(f"Processed a total of {len(all_speakers)} speakers across {page_num} pages")
        
        # Save the final data to JSON and CSV files
        save_to_json(all_speakers)
        save_to_csv(all_speakers)
        
        logger.info("Scraping completed successfully")
        
        # Close the browser
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())