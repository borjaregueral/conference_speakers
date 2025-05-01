"""
Data utilities for the World Retail Congress Speakers Scraper.

This module contains utility functions for data handling.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List

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