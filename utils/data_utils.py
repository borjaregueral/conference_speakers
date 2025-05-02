"""
Data utilities for the World Retail Congress Speakers Scraper.

This module contains utility functions for data handling.
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import time

import openai
from dotenv import load_dotenv

import config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def save_to_json(data: List[Dict], filename: Path) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: List of dictionaries containing the data
        filename: Path to the JSON file to save to
    """
    if not data:
        logger.warning("No data to save to JSON")
        return
    
    try:
        logger.info(f"Saving {len(data)} records to {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, indent=2, ensure_ascii=False, fp=f)
        logger.info(f"Successfully saved data to {filename}")
    except Exception as e:
        logger.error(f"Error saving data to JSON: {e}")


def save_to_csv(data: List[Dict], filename: Path) -> None:
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries containing the data
        filename: Path to the CSV file to save to
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


def load_json(filename: Path) -> List[Dict]:
    """
    Load data from a JSON file.
    
    Args:
        filename: Path to the JSON file to load from
        
    Returns:
        List of dictionaries containing the data
    """
    try:
        logger.info(f"Loading data from {filename}")
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {len(data)} records from {filename}")
        return data
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {filename}")
        return []
    except Exception as e:
        logger.error(f"Error loading data from JSON: {e}")
        return []


def enrich_company_data(speaker_collection, api_key: Optional[str] = None) -> bool:
    """
    Enrich speaker data with company information using OpenAI with web browsing capability.
    
    Args:
        speaker_collection: SpeakerCollection object containing speakers
        api_key: Optional OpenAI API key (if not provided, will use OPENAI_API_KEY env var)
        
    Returns:
        bool: True if enrichment was successful, False otherwise
    """
    # Set up OpenAI client
    if api_key:
        openai.api_key = api_key
        logger.info("Using provided API key")
    else:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        logger.info(f"Using API key from environment: {openai.api_key[:4]}...{openai.api_key[-4:] if openai.api_key else 'None'}")
        
    if not openai.api_key or openai.api_key == "your_openai_api_key_here":
        logger.error("Valid OpenAI API key not found. Cannot enrich company data.")
        logger.error("Please set a valid OPENAI_API_KEY in your .env file or environment variables.")
        return False
    
    # Count speakers that need enrichment
    speakers_to_enrich = []
    for speaker in speaker_collection.speakers:
        # Skip speakers that have no company information
        if speaker.company == "Unknown" or speaker.company == "Not available":
            continue
        
        # Skip speakers that have already been enriched - more robust check
        if (speaker.company_type not in ["Not available", ""] and
            speaker.company_size not in ["Not available", ""] and
            speaker.company_hq_country not in ["Not available", ""]):
            continue
            
        speakers_to_enrich.append(speaker)
    
    if not speakers_to_enrich:
        logger.info("No speakers need enrichment - all speakers already enriched or have no company information")
        return True
        
    logger.info(f"Starting company data enrichment for {len(speakers_to_enrich)} speakers that need enrichment")
    
    # Process each speaker that needs enrichment
    for i, speaker in enumerate(speakers_to_enrich):
        logger.info(f"Enriching company data for {speaker.name} ({speaker.company}) - {i+1}/{len(speakers_to_enrich)}")
        
        try:
            # Create system message with instructions for web browsing
            system_message = """
            You are a company research assistant with web browsing capabilities. Your task is to find accurate
            information about companies and return it in a structured format. Always search the web for the
            most up-to-date information about the company you're researching.
            
            For each company, you need to find:
            1. Company type/industry (e.g., Retail, Technology, Finance)
            2. Company size (approximate number of employees)
            3. Headquarters address (full address if available)
            4. Headquarters country
            5. International status (Yes/No - does the company have offices in multiple countries?)
            
            Return ONLY a JSON object with these keys:
            - company_type
            - company_size
            - company_hq_address
            - company_hq_country
            - company_international
            
            If you cannot find specific information after searching, use "Not available" as the value.
            """
            
            # Create user message with company to research
            user_message = f"""
            Research the company "{speaker.company}" and provide the requested information.
            
            If the company name is ambiguous or could refer to multiple entities, use additional context from
            this person's information to determine the correct company:
            - Person's name: {speaker.name}
            - Person's position: {speaker.position}
            - Description: {speaker.description[:200]}...
            
            Return only the JSON object with the requested information.
            """
            
            # Call OpenAI API with browsing enabled
            response = openai.chat.completions.create(
                model="gpt-4-turbo",  # Using a model that supports browsing
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=1000,
                response_format={"type": "json_object"}  # Request JSON response
            )
            
            # Extract the response content
            result_text = response.choices[0].message.content.strip()
            
            try:
                # Parse the JSON response
                company_data = json.loads(result_text)
                
                # Update speaker with company information
                speaker.company_type = company_data.get("company_type", "Not available")
                speaker.company_size = company_data.get("company_size", "Not available")
                speaker.company_hq_address = company_data.get("company_hq_address", "Not available")
                speaker.company_hq_country = company_data.get("company_hq_country", "Not available")
                speaker.company_international = company_data.get("company_international", "Not available")
                
                logger.info(f"Successfully enriched company data for {speaker.name} ({speaker.company})")
                logger.info(f"  Type: {speaker.company_type}")
                logger.info(f"  Size: {speaker.company_size}")
                logger.info(f"  HQ: {speaker.company_hq_address}, {speaker.company_hq_country}")
                logger.info(f"  International: {speaker.company_international}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response for {speaker.name}: {e}")
                logger.error(f"Response content: {result_text[:100]}...")
                
            # Add a delay to avoid rate limiting
            time.sleep(1.0)
            
        except Exception as e:
            logger.error(f"Error enriching company data for {speaker.name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
    logger.info("Company data enrichment completed")
    return True