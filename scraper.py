#!/usr/bin/env python3
"""
World Retail Congress Speakers Scraper

This script scrapes speaker information from the World Retail Congress website
using Playwright for browser automation.
"""

import asyncio
import csv
import json
import logging
import os
import re
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Page

from config import BASE_URL, SPEAKERS_URL, OUTPUT_JSON_FILE, OUTPUT_CSV_FILE, GENERIC_DESCRIPTION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# # Constants
# BASE_URL = "https://www.worldretailcongress.com"
# SPEAKERS_URL = f"{BASE_URL}/2025-speakers"
# OUTPUT_JSON_FILE = "speakers.json"
# OUTPUT_CSV_FILE = "speakers.csv"
# GENERIC_DESCRIPTION = "Since 2007, World Retail Congress has been the premier platform for in-depth research, content and events; driving retail growth and inspiring valuable global connections."


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


async def extract_speaker_details(page: Page, browser, speaker: Dict) -> Dict:
    """
    Extract detailed information for a speaker by navigating to their page.
    
    Args:
        page: The Playwright page object
        browser: The Playwright browser object
        speaker: Dictionary containing basic speaker information
        
    Returns:
        Dictionary containing detailed speaker information
    """
    try:
        speaker_name = speaker['name']
        logger.info(f"Extracting details for speaker: {speaker_name}")
        
        # Check if we have a speaker URL
        if speaker.get('speakerUrl'):
            speaker_url = speaker['speakerUrl']
            
            # If the URL doesn't start with http, assume it's a relative URL
            if not speaker_url.startswith('http'):
                speaker_url = f"{BASE_URL}/{speaker_url}"
                
            logger.info(f"Navigating to speaker page: {speaker_url}")
            
            # Open a new page for the speaker
            speaker_page = await browser.new_page()
            await speaker_page.goto(speaker_url)
            await speaker_page.wait_for_load_state("networkidle")
            
            # Accept cookies if needed
            await accept_cookies(speaker_page)
            
            # Extract detailed information with improved selectors
            detail_data = await speaker_page.evaluate(f"""
            () => {{
                // Function to clean text (remove extra whitespace, newlines, etc.)
                function cleanText(text) {{
                    if (!text) return '';
                    return text.replace(/\\s+/g, ' ').trim();
                }}
                
                // Function to check if text is from a cookie consent banner
                function isCookieConsentText(text) {{
                    if (!text) return false;
                    
                    const cookieKeywords = [
                        'cookie', 'consent', 'privacy', 'necessary cookies', 
                        'data protection', 'gdpr', 'personal data', 
                        'tracking', 'third party', 'third-party'
                    ];
                    
                    const lowerText = text.toLowerCase();
                    return cookieKeywords.some(keyword => lowerText.includes(keyword.toLowerCase()));
                }}
                
                // Function to check if text is the generic description
                function isGenericDescription(text) {{
                    if (!text) return false;
                    
                    const genericDesc = "{GENERIC_DESCRIPTION}";
                    return text.includes(genericDesc);
                }}
                
                // Extract description - look for paragraphs
                let description = 'No description available';
                const paragraphs = document.querySelectorAll('p');
                if (paragraphs.length > 0) {{
                    // Use the longest paragraph as the description
                    let longestText = '';
                    for (const p of paragraphs) {{
                        const text = p.textContent.trim();
                        // Skip cookie consent text and generic description
                        if (text.length > longestText.length && 
                            !isCookieConsentText(text) && 
                            !isGenericDescription(text)) {{
                            longestText = text;
                        }}
                    }}
                    if (longestText) {{
                        description = longestText;
                    }}
                }}
                
                // Extract session information
                let sessionInfo = {{
                    title: 'Not available',
                    date: 'Not available',
                    time: 'Not available',
                    venue: 'Not available'
                }};
                
                // Look for elements that might contain session information
                const sessionElements = document.querySelectorAll('.session-title, [class*="session"], [class*="talk"], [class*="presentation"]');
                for (const el of sessionElements) {{
                    const text = cleanText(el.textContent);
                    if (text && text.length > 0 && 
                        text !== 'We value your privacy' && 
                        !isCookieConsentText(text)) {{
                        
                        // Try to parse the session information
                        // Example format: "Sessions 13-May-2025 12:10 – 12:50 Track 2 Debate: From Traffic to Revenue: Unlock Platform Success with Retail Media"
                        
                        // Extract date
                        const dateMatch = text.match(/(\\d{{1,2}})[-–]May[-–](\\d{{4}})/);
                        if (dateMatch) {{
                            sessionInfo.date = `${{dateMatch[1]}} May ${{dateMatch[2]}}`;
                        }}
                        
                        // Extract time
                        const timeMatch = text.match(/(\\d{{1,2}}:\\d{{2}})\\s*[–-]\\s*(\\d{{1,2}}:\\d{{2}})/);
                        if (timeMatch) {{
                            sessionInfo.time = `${{timeMatch[1]}} - ${{timeMatch[2]}}`;
                        }}
                        
                        // Extract venue (Track or Suite)
                        const venueMatch = text.match(/Track\\s*(\\d+)|([\\w\\s]+Suite)/);
                        if (venueMatch) {{
                            sessionInfo.venue = venueMatch[0];
                        }}
                        
                        // Extract title - assume it's after "Debate:" or similar keywords
                        const titleMatch = text.match(/(?:Debate|Briefing|Keynote|Panel|Fireside Chat|Workshop|Presentation):\\s*(.+)$/);
                        if (titleMatch) {{
                            sessionInfo.title = titleMatch[1].trim();
                        }} else {{
                            // If no specific keyword, just use the last part of the text
                            const parts = text.split(':');
                            if (parts.length > 1) {{
                                sessionInfo.title = parts[parts.length - 1].trim();
                            }}
                        }}
                        
                        break;
                    }}
                }}
                
                // If session title not found, try other heading elements
                if (sessionInfo.title === 'Not available') {{
                    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    for (const h of headings) {{
                        const text = cleanText(h.textContent);
                        // Skip common navigation/website headings and cookie consent text
                        if (text && text.length > 0 && 
                            !text.includes('About') && 
                            !text.includes('Programme') && 
                            !text.includes('Sponsor') && 
                            !text.includes('Insights') &&
                            !text.includes('BOOK YOUR PLACE') &&
                            !text.includes('We value your privacy') &&
                            !isCookieConsentText(text)) {{
                            
                            // Check if it's a session title
                            if (text.includes('Debate:') || 
                                text.includes('Briefing:') || 
                                text.includes('Keynote:') || 
                                text.includes('Panel:')) {{
                                
                                // Extract the title part
                                const titleMatch = text.match(/(?:Debate|Briefing|Keynote|Panel|Fireside Chat|Workshop|Presentation):\\s*(.+)$/);
                                if (titleMatch) {{
                                    sessionInfo.title = titleMatch[1].trim();
                                }} else {{
                                    sessionInfo.title = text;
                                }}
                                break;
                            }}
                        }}
                    }}
                }}
                
                // Extract date/time if not found in session info
                if (sessionInfo.date === 'Not available' || sessionInfo.time === 'Not available') {{
                    const dateElements = document.querySelectorAll('[class*="date"], [class*="time"], [class*="schedule"], time');
                    for (const el of dateElements) {{
                        const text = cleanText(el.textContent);
                        if (text && text.length > 0 && 
                            !text.includes('About') && 
                            !text.includes('Programme') && 
                            !text.includes('Sponsor') && 
                            !text.includes('Insights') &&
                            !isCookieConsentText(text)) {{
                            
                            // Extract date
                            const dateMatch = text.match(/(\\d{{1,2}})(?:st|nd|rd|th)?\\s*[-–]\\s*(\\d{{1,2}})(?:st|nd|rd|th)?\\s*May\\s*(\\d{{4}})?/);
                            if (dateMatch) {{
                                sessionInfo.date = dateMatch[0];
                            }}
                            
                            // Extract time
                            const timeMatch = text.match(/(\\d{{1,2}}:\\d{{2}})\\s*[-–]\\s*(\\d{{1,2}}:\\d{{2}})/);
                            if (timeMatch) {{
                                sessionInfo.time = `${{timeMatch[1]}} - ${{timeMatch[2]}}`;
                            }}
                            
                            break;
                        }}
                    }}
                }}
                
                // If venue not found in session info, look for it separately
                if (sessionInfo.venue === 'Not available') {{
                    const venueElements = document.querySelectorAll('[class*="location"], [class*="venue"], [class*="place"], [class*="track"]');
                    for (const el of venueElements) {{
                        const text = cleanText(el.textContent);
                        if (text && text.length > 0 && 
                            (text.includes('Track') || 
                             text.includes('Room') || 
                             text.includes('Hall') || 
                             text.includes('Suite') ||
                             text.includes('Stage')) &&
                            !isCookieConsentText(text)) {{
                            sessionInfo.venue = text;
                            break;
                        }}
                    }}
                    
                    // If still not found, look for location keywords
                    if (sessionInfo.venue === 'Not available') {{
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {{
                            const text = cleanText(el.textContent);
                            if ((text.includes('Track') || 
                                text.includes('Room') || 
                                text.includes('Hall') || 
                                text.includes('Suite') ||
                                text.includes('Stage')) &&
                                !isCookieConsentText(text)) {{
                                
                                // Extract just the venue part
                                const venueMatch = text.match(/Track\\s*(\\d+)|([\\w\\s]+Suite)/);
                                if (venueMatch) {{
                                    sessionInfo.venue = venueMatch[0];
                                    break;
                                }}
                            }}
                        }}
                    }}
                }}
                
                // Clean up the date field
                if (sessionInfo.date.includes('12th - 14th May 2025')) {{
                    sessionInfo.date = '12th - 14th May 2025';
                }}
                
                return {{
                    description,
                    session_title: sessionInfo.title,
                    date: sessionInfo.date,
                    time: sessionInfo.time,
                    venue: sessionInfo.venue
                }};
            }}
            """)
            
            # Close the speaker page
            await speaker_page.close()
            
            # Combine basic and detailed information
            return {
                'name': speaker_name,
                'position': speaker.get('position', 'Unknown'),
                'company': speaker.get('company', 'Unknown'),
                'description': detail_data.get('description', 'No description available'),
                'session_title': detail_data.get('session_title', 'Not available'),
                'date': detail_data.get('date', 'Not available'),
                'time': detail_data.get('time', 'Not available'),
                'location': detail_data.get('venue', 'Not available')
            }
        else:
            logger.warning(f"No speaker URL found for {speaker_name}")
            return {
                'name': speaker_name,
                'position': speaker.get('position', 'Unknown'),
                'company': speaker.get('company', 'Unknown'),
                'description': 'No description available',
                'session_title': 'Not available',
                'date': 'Not available',
                'time': 'Not available',
                'location': 'Not available'
            }
        
    except Exception as e:
        logger.error(f"Error extracting details for speaker: {e}")
        return {
            'name': speaker['name'],
            'position': speaker.get('position', 'Unknown'),
            'company': speaker.get('company', 'Unknown'),
            'description': 'No description available',
            'session_title': 'Error',
            'date': 'Error',
            'time': 'Error',
            'location': 'Error'
        }


def save_to_csv(data: List[Dict], filename: str) -> None:
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries containing the data
        filename: Name of the CSV file to save to
    """
    if not data:
        logger.warning("No data to save to CSV")
        return
    
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
                        with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
                            json.dump(all_speakers, indent=2, ensure_ascii=False, fp=f)
                        save_to_csv(all_speakers, OUTPUT_CSV_FILE)
                    
                except Exception as e:
                    logger.error(f"Error processing speaker {speaker['name']}: {e}")
        
        logger.info(f"Processed a total of {len(all_speakers)} speakers across {page_num} pages")
        
        # Save the final data to JSON and CSV files
        logger.info(f"Saving {len(all_speakers)} speakers to {OUTPUT_JSON_FILE}")
        with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(all_speakers, indent=2, ensure_ascii=False, fp=f)
        
        # Save to CSV
        save_to_csv(all_speakers, OUTPUT_CSV_FILE)
        
        logger.info("Scraping completed successfully")
        
        # Close the browser
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())