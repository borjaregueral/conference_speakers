"""
Speaker model for the World Retail Congress Speakers Scraper.

This module defines the Speaker data model.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class Speaker:
    """Speaker data model."""
    name: str
    position: str = "Unknown"
    company: str = "Unknown"
    description: str = "No description available"
    session_title: str = "Not available"
    date: str = "Not available"
    time: str = "Not available"
    location: str = "Not available"
    # Company enrichment fields
    company_type: str = "Not available"
    company_size: str = "Not available"
    company_hq_address: str = "Not available"
    company_hq_country: str = "Not available"
    company_international: str = "Not available"
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Speaker':
        """Create a Speaker instance from a dictionary."""
        return cls(
            name=data.get('name', 'Unknown'),
            position=data.get('position', 'Unknown'),
            company=data.get('company', 'Unknown'),
            description=data.get('description', 'No description available'),
            session_title=data.get('session_title', 'Not available'),
            date=data.get('date', 'Not available'),
            time=data.get('time', 'Not available'),
            location=data.get('location', 'Not available'),
            # Company enrichment fields
            company_type=data.get('company_type', 'Not available'),
            company_size=data.get('company_size', 'Not available'),
            company_hq_address=data.get('company_hq_address', 'Not available'),
            company_hq_country=data.get('company_hq_country', 'Not available'),
            company_international=data.get('company_international', 'Not available')
        )
    
    def to_dict(self) -> Dict:
        """Convert the Speaker instance to a dictionary."""
        return asdict(self)


class SpeakerCollection:
    """Collection of Speaker objects."""
    
    def __init__(self, speakers: Optional[List[Speaker]] = None):
        """Initialize the collection with optional speakers."""
        self.speakers = speakers or []
    
    def add(self, speaker: Speaker) -> None:
        """Add a speaker to the collection."""
        self.speakers.append(speaker)
    
    def get_all(self) -> List[Speaker]:
        """Get all speakers in the collection."""
        return self.speakers
    
    def get_by_name(self, name: str) -> Optional[Speaker]:
        """Get a speaker by name."""
        for speaker in self.speakers:
            if speaker.name.lower() == name.lower():
                return speaker
        return None
    
    def get_by_company(self, company: str) -> List[Speaker]:
        """Get all speakers from a specific company."""
        return [s for s in self.speakers if company.lower() in s.company.lower()]
    
    def get_by_date(self, date: str) -> List[Speaker]:
        """Get all speakers speaking on a specific date."""
        return [s for s in self.speakers if date.lower() in s.date.lower()]
    
    def to_dict_list(self) -> List[Dict]:
        """Convert all speakers to a list of dictionaries."""
        return [speaker.to_dict() for speaker in self.speakers]
    
    @classmethod
    def from_dict_list(cls, dict_list: List[Dict]) -> 'SpeakerCollection':
        """Create a SpeakerCollection from a list of dictionaries."""
        speakers = [Speaker.from_dict(d) for d in dict_list]
        return cls(speakers)