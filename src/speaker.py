"""
Speaker module for the World Retail Congress Speakers Scraper.

This module contains functions for extracting speaker information.
"""

import logging
from typing import Dict

from playwright.async_api import Page, Browser

from src.paths import BASE_URL
from src.utils import GENERIC_DESCRIPTION, accept_cookies

# Configure logging
logger = logging.getLogger(__name__)


async def extract_speaker_details(page: Page, browser: Browser, speaker: Dict) -> Dict:
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