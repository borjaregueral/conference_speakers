#!/usr/bin/env python3
"""
Entry point script for the World Retail Congress Speakers Scraper.

This script simply imports and runs the main function from the src.main module.
"""

import asyncio
from src.main import main

if __name__ == "__main__":
    asyncio.run(main())