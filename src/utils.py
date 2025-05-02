"""
Utilities module for the World Retail Congress Speakers Scraper.

This module contains utility functions used throughout the application.
"""

import csv
import json
import logging
from typing import Dict, List

from playwright.async_api import Page

from config import OUTPUT_JSON_FILE, OUTPUT_CSV_FILE

# Constants
GENERIC_DESCRIPTION = "No description available"

# Configure logging
logger = logging.getLogger(__name__)


async def accept_cookies(page: Page) -> None:
    """Accept cookies on the page if the cookie banner is present."""
    try:
        # Wait for the cookie banner to appear
        logger.info("Looking for cookie consent banner...")
        
        # Try JavaScript approach with multiple attempts
        for attempt in range(3):
            clicked = await page.evaluate("""
            () => {
                // Try multiple approaches to find and click the cookie button
                
                // Approach 1: Find by data-cky-tag attribute
                const acceptButton = document.querySelector('button[data-cky-tag="accept-button"]');
                if (acceptButton) {
                    console.log('Found cookie button by data-cky-tag');
                    acceptButton.click();
                    return true;
                }
                
                // Approach 2: Find by aria-label
                const ariaButton = document.querySelector('button[aria-label="Accept All"]');
                if (ariaButton) {
                    console.log('Found cookie button by aria-label');
                    ariaButton.click();
                    return true;
                }
                
                // Approach 3: Find by class
                const classButton = document.querySelector('.cky-btn-accept');
                if (classButton) {
                    console.log('Found cookie button by class');
                    classButton.click();
                    return true;
                }
                
                // Approach 4: Find any button with "Accept All" text
                const buttons = Array.from(document.querySelectorAll('button'));
                const acceptAllButton = buttons.find(btn => 
                    btn.textContent.includes('Accept All')
                );
                
                if (acceptAllButton) {
                    console.log('Found Accept All button by text content');
                    acceptAllButton.click();
                    return true;
                }
                
                // Approach 5: Find any button with "Accept" text
                const acceptButton2 = buttons.find(btn => 
                    btn.textContent.includes('Accept') || 
                    btn.textContent.includes('accept')
                );
                
                if (acceptButton2) {
                    console.log('Found Accept button by text content');
                    acceptButton2.click();
                    return true;
                }
                
                // Approach 6: Try clicking on any element that looks like a cookie banner button
                const cookieBannerButtons = document.querySelectorAll('[class*="cookie"] button, [class*="consent"] button, [class*="privacy"] button');
                if (cookieBannerButtons.length > 0) {
                    console.log('Found cookie banner button by class pattern');
                    cookieBannerButtons[0].click();
                    return true;
                }
                
                return false;
            }
            """)
            
            if clicked:
                logger.info("Successfully clicked cookie button via JavaScript")
                await page.wait_for_timeout(1000)
                return
            else:
                logger.warning(f"Could not find cookie button via JavaScript (attempt {attempt+1}/3)")
                await page.wait_for_timeout(1000)  # Wait a bit and try again
        
        # If we get here, we couldn't click the cookie button with JavaScript
        # Try clicking with Playwright's built-in methods
        try:
            # Look for common cookie consent button selectors
            for selector in [
                'button[data-cky-tag="accept-button"]',
                'button[aria-label="Accept All"]',
                '.cky-btn-accept',
                'button:has-text("Accept All")',
                'button:has-text("Accept")',
                '[class*="cookie"] button',
                '[class*="consent"] button',
                '[class*="privacy"] button'
            ]:
                if await page.query_selector(selector):
                    await page.click(selector)
                    logger.info(f"Successfully clicked cookie button using selector: {selector}")
                    await page.wait_for_timeout(1000)
                    return
        except Exception as e:
            logger.warning(f"Error clicking cookie button with Playwright: {e}")
            
    except Exception as e:
        logger.warning(f"Could not find or click cookie consent button: {e}")


async def find_speaker_links(page: Page) -> List[Dict]:
    """
    Find all speaker links on the page.
    
    Args:
        page: The Playwright page object
        
    Returns:
        List of dictionaries containing speaker information
    """
    logger.info("Finding speaker links on the page...")
    
    # Get all speaker cards
    speaker_cards = await page.evaluate("""
    () => {
        // Find all speaker cards
        const speakerItems = document.querySelectorAll('.m-speakers-list__items__item, [class*="speaker-item"]');
        
        return Array.from(speakerItems).map(item => {
            // Find the link, name, position, and company
            const link = item.querySelector('a');
            const nameEl = item.querySelector('h2, h3, h4, [class*="name"]');
            const positionEl = item.querySelector('[class*="position"], [class*="job"]');
            const companyEl = item.querySelector('[class*="company"], [class*="organization"]');
            
            // Get the onclick attribute or href that contains openRemoteModal
            let modalInfo = null;
            let speakerUrl = null;
            
            if (link) {
                const onclick = link.getAttribute('onclick');
                const href = link.getAttribute('href');
                
                if (onclick && onclick.includes('openRemoteModal')) {
                    modalInfo = onclick;
                    
                    // Extract the speaker URL from the modalInfo
                    const match = onclick.match(/openRemoteModal\\('([^']+)'/);
                    if (match) {
                        speakerUrl = match[1];
                    }
                } else if (href && href.includes('openRemoteModal')) {
                    modalInfo = href;
                    
                    // Extract the speaker URL from the href
                    const match = href.match(/openRemoteModal\\('([^']+)'/);
                    if (match) {
                        speakerUrl = match[1];
                    }
                } else if (href) {
                    speakerUrl = href;
                }
            }
            
            return {
                name: nameEl ? nameEl.textContent.trim() : 'Unknown',
                position: positionEl ? positionEl.textContent.trim() : 'Unknown',
                company: companyEl ? companyEl.textContent.trim() : 'Unknown',
                modalInfo: modalInfo,
                speakerUrl: speakerUrl
            };
        });
    }
    """)
    
    logger.info(f"Found {len(speaker_cards)} speaker cards on current page")
    return speaker_cards


async def check_for_pagination(page: Page) -> bool:
    """
    Check if there are more pages of speakers.
    
    Args:
        page: The Playwright page object
        
    Returns:
        True if there is a next page, False otherwise
    """
    # Check for pagination elements
    has_next_page = await page.evaluate("""
    () => {
        // Look for pagination elements at the bottom of the page
        const paginationElements = document.querySelectorAll('.pagination, [class*="pagination"], [class*="pager"], nav[aria-label*="pagination"]');
        
        if (paginationElements.length === 0) {
            console.log('No pagination elements found');
            return false;
        }
        
        // Look for "Next" or ">" links within pagination elements
        let hasNextPage = false;
        
        paginationElements.forEach(pagination => {
            const nextLinks = Array.from(pagination.querySelectorAll('a, button')).filter(el => {
                const text = el.textContent.trim().toLowerCase();
                return text === 'next' || 
                       text === '>' || 
                       text === 'next page' || 
                       text === '→' ||
                       el.getAttribute('aria-label')?.toLowerCase().includes('next');
            });
            
            // Check if the next link is disabled
            const isDisabled = nextLinks.some(link => 
                link.hasAttribute('disabled') || 
                link.classList.contains('disabled') ||
                link.parentElement.classList.contains('disabled')
            );
            
            if (nextLinks.length > 0 && !isDisabled) {
                console.log('Found next page link in pagination');
                hasNextPage = true;
            }
        });
        
        return hasNextPage;
    }
    """)
    
    logger.info(f"Pagination check: {'Next page available' if has_next_page else 'No more pages'}")
    return has_next_page


async def go_to_next_page(page: Page) -> bool:
    """
    Navigate to the next page of speakers.
    
    Args:
        page: The Playwright page object
        
    Returns:
        True if successfully navigated to the next page, False otherwise
    """
    # Try to click the next page link
    clicked = await page.evaluate("""
    () => {
        // Look for pagination elements at the bottom of the page
        const paginationElements = document.querySelectorAll('.pagination, [class*="pagination"], [class*="pager"], nav[aria-label*="pagination"]');
        
        if (paginationElements.length === 0) {
            console.log('No pagination elements found');
            return false;
        }
        
        // Look for "Next" or ">" links within pagination elements
        let nextLinkClicked = false;
        
        paginationElements.forEach(pagination => {
            if (nextLinkClicked) return;
            
            const nextLinks = Array.from(pagination.querySelectorAll('a, button')).filter(el => {
                const text = el.textContent.trim().toLowerCase();
                return text === 'next' || 
                       text === '>' || 
                       text === 'next page' || 
                       text === '→' ||
                       el.getAttribute('aria-label')?.toLowerCase().includes('next');
            });
            
            // Check if the next link is disabled
            const isDisabled = nextLinks.some(link => 
                link.hasAttribute('disabled') || 
                link.classList.contains('disabled') ||
                link.parentElement.classList.contains('disabled')
            );
            
            if (nextLinks.length > 0 && !isDisabled) {
                console.log('Clicking next page link in pagination');
                nextLinks[0].click();
                nextLinkClicked = true;
            }
        });
        
        return nextLinkClicked;
    }
    """)
    
    if clicked:
        logger.info("Clicked next page link")
        await page.wait_for_load_state("networkidle")
        return True
    else:
        logger.warning("Could not find or click next page link")
        return False


def save_to_csv(data: List[Dict], filename=None) -> None:
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries containing the data
        filename: Name of the CSV file to save to (defaults to OUTPUT_CSV_FILE)
    """
    if not data:
        logger.warning("No data to save to CSV")
        return
    
    if filename is None:
        filename = OUTPUT_CSV_FILE
    
    try:
        logger.info(f"Saving {len(data)} records to {filename}")
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Get field names from the first dictionary
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            writer.writerows(data)
            
        logger.info(f"Successfully saved data to {filename}")
    except Exception as e:
        logger.error(f"Error saving data to CSV: {e}")


def save_to_json(data: List[Dict], filename=None) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: List of dictionaries containing the data
        filename: Name of the JSON file to save to (defaults to OUTPUT_JSON_FILE)
    """
    if not data:
        logger.warning("No data to save to JSON")
        return
    
    if filename is None:
        filename = OUTPUT_JSON_FILE
    
    try:
        logger.info(f"Saving {len(data)} records to {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, indent=2, ensure_ascii=False, fp=f)
        logger.info(f"Successfully saved data to {filename}")
    except Exception as e:
        logger.error(f"Error saving data to JSON: {e}")