"""
Scraper controller for the World Retail Congress Speakers Scraper.

This module contains the controller for scraping speaker data.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright, Page, Browser

import config
from models.speaker import Speaker, SpeakerCollection
from utils.data_utils import save_to_json, save_to_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ScraperController:
    """Controller for scraping speaker data."""
    
    def __init__(self):
        """Initialize the scraper controller."""
        self.speaker_collection = SpeakerCollection()
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup_browser(self) -> None:
        """Set up the browser for scraping."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=config.HEADLESS_MODE)
        self.context = await self.browser.new_context(
            viewport={'width': config.VIEWPORT_WIDTH, 'height': config.VIEWPORT_HEIGHT}
        )
        self.page = await self.context.new_page()
    
    async def teardown_browser(self) -> None:
        """Close the browser."""
        if self.browser:
            await self.browser.close()
    
    async def accept_cookies(self, page: Page) -> None:
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
    
    async def find_speaker_links(self, page: Page) -> List[Dict]:
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
    
    async def extract_speaker_details(self, page: Page, browser: Browser, speaker: Dict) -> Speaker:
        """
        Extract detailed information for a speaker by navigating to their page.
        
        Args:
            page: The Playwright page object
            browser: The Playwright browser object
            speaker: Dictionary containing basic speaker information
            
        Returns:
            Speaker object with detailed information
        """
        try:
            speaker_name = speaker['name']
            logger.info(f"Extracting details for speaker: {speaker_name}")
            
            # Check if we have a speaker URL
            if speaker.get('speakerUrl'):
                speaker_url = speaker['speakerUrl']
                
                # If the URL doesn't start with http, assume it's a relative URL
                if not speaker_url.startswith('http'):
                    speaker_url = f"{config.BASE_URL}/{speaker_url}"
                    
                logger.info(f"Navigating to speaker page: {speaker_url}")
                
                # Open a new page for the speaker
                speaker_page = await browser.new_page()
                await speaker_page.goto(speaker_url)
                await speaker_page.wait_for_load_state("networkidle")
                
                # Accept cookies if needed
                await self.accept_cookies(speaker_page)
                
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
                    
                    // Extract description - look for paragraphs
                    let description = 'No description available';
                    const paragraphs = document.querySelectorAll('p');
                    if (paragraphs.length > 0) {{
                        // Use the longest paragraph as the description
                        let longestText = '';
                        for (const p of paragraphs) {{
                            const text = p.textContent.trim();
                            // Skip cookie consent text
                            if (text.length > longestText.length && !isCookieConsentText(text)) {{
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
                
                # Create a Speaker object
                return Speaker(
                    name=speaker_name,
                    position=speaker.get('position', 'Unknown'),
                    company=speaker.get('company', 'Unknown'),
                    description=detail_data.get('description', 'No description available'),
                    session_title=detail_data.get('session_title', 'Not available'),
                    date=detail_data.get('date', 'Not available'),
                    time=detail_data.get('time', 'Not available'),
                    location=detail_data.get('venue', 'Not available')
                )
            else:
                logger.warning(f"No speaker URL found for {speaker_name}")
                return Speaker(
                    name=speaker_name,
                    position=speaker.get('position', 'Unknown'),
                    company=speaker.get('company', 'Unknown')
                )
            
        except Exception as e:
            logger.error(f"Error extracting details for speaker: {e}")
            return Speaker(
                name=speaker['name'],
                position=speaker.get('position', 'Unknown'),
                company=speaker.get('company', 'Unknown'),
                session_title='Error',
                date='Error',
                time='Error',
                location='Error'
            )
    
    async def scrape_speakers(self) -> SpeakerCollection:
        """
        Scrape speaker information from the World Retail Congress website.
        
        Returns:
            SpeakerCollection containing all scraped speakers
        """
        try:
            await self.setup_browser()
            
            # Process all pages of speakers
            all_speakers = []
            
            # Process pages
            for page_num in range(1, config.MAX_PAGES + 1):
                # Navigate to the page
                if page_num == 1:
                    logger.info(f"Navigating to {config.SPEAKERS_URL}")
                    await self.page.goto(config.SPEAKERS_URL)
                else:
                    logger.info(f"Navigating to page {page_num}")
                    page_url = f"{config.SPEAKERS_URL}?page={page_num}"
                    await self.page.goto(page_url)
                
                await self.page.wait_for_load_state("networkidle")
                
                # Accept cookies if needed
                await self.accept_cookies(self.page)
                
                logger.info(f"Processing page {page_num} of speakers")
                
                # Find all speaker links on the current page
                speakers_on_page = await self.find_speaker_links(self.page)
                
                # If no speakers found on this page, break the loop
                if not speakers_on_page:
                    logger.info(f"No speakers found on page {page_num}, stopping")
                    break
                
                logger.info(f"Found {len(speakers_on_page)} speakers on page {page_num}")
                
                # Process each speaker on the current page
                for i, speaker_dict in enumerate(speakers_on_page):
                    try:
                        # Extract details for this speaker
                        speaker = await self.extract_speaker_details(self.page, self.browser, speaker_dict)
                        
                        # Add to collection
                        self.speaker_collection.add(speaker)
                        
                        # Print the extracted information
                        logger.info(f"Successfully extracted information for {speaker.name} ({i+1}/{len(speakers_on_page)})")
                        description_preview = speaker.description[:100] + "..." if len(speaker.description) > 100 else speaker.description
                        logger.info(f"Description: {description_preview}")
                        logger.info(f"Session title: {speaker.session_title}")
                        logger.info(f"Date: {speaker.date}")
                        logger.info(f"Time: {speaker.time}")
                        logger.info(f"Location: {speaker.location}")
                        
                        # Save progress at intervals
                        if len(self.speaker_collection.speakers) % config.SAVE_PROGRESS_INTERVAL == 0:
                            logger.info(f"Saving progress ({len(self.speaker_collection.speakers)} speakers processed)")
                            self.save_data()
                        
                    except Exception as e:
                        logger.error(f"Error processing speaker {speaker_dict.get('name', 'Unknown')}: {e}")
            
            logger.info(f"Processed a total of {len(self.speaker_collection.speakers)} speakers")
            
            # Save the final data
            self.save_data()
            
            logger.info("Scraping completed successfully")
            
            return self.speaker_collection
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return self.speaker_collection
        finally:
            # Close the browser
            await self.teardown_browser()
    
    def save_data(self) -> None:
        """Save the speaker data to JSON and CSV files."""
        # Convert to list of dictionaries
        data = self.speaker_collection.to_dict_list()
        
        # Save to JSON
        save_to_json(data, config.OUTPUT_JSON_FILE)
        
        # Save to CSV
        save_to_csv(data, config.OUTPUT_CSV_FILE)
    
    @classmethod
    def load_data(cls) -> SpeakerCollection:
        """
        Load speaker data from the JSON file.
        
        Returns:
            SpeakerCollection containing the loaded speakers
        """
        try:
            with open(config.OUTPUT_JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SpeakerCollection.from_dict_list(data)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"Could not load data from {config.OUTPUT_JSON_FILE}")
            return SpeakerCollection()


# Function to run the scraper
async def run_scraper() -> SpeakerCollection:
    """
    Run the scraper to collect speaker data.
    
    Returns:
        SpeakerCollection containing all scraped speakers
    """
    controller = ScraperController()
    return await controller.scrape_speakers()