"""
Streamlit view for the World Retail Congress Speakers Scraper.

This module contains the Streamlit UI for displaying and interacting with speaker data.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from controllers.scraper_controller import ScraperController, run_scraper
from models.speaker import Speaker, SpeakerCollection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class StreamlitView:
    """Streamlit view for the World Retail Congress Speakers Scraper."""
    
    def __init__(self):
        """Initialize the Streamlit view."""
        self.speaker_collection = None
        self.scraper_controller = ScraperController()
        self.setup_page()
    
    def setup_page(self):
        """Set up the Streamlit page."""
        st.set_page_config(
            page_title=config.STREAMLIT_TITLE,
            page_icon=config.STREAMLIT_FAVICON,
            layout="wide",
            initial_sidebar_state="expanded",
        )
        
        st.title(config.STREAMLIT_TITLE)
        st.sidebar.title("Controls")
    
    def load_data(self) -> bool:
        """
        Load speaker data from file.
        
        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            self.speaker_collection = self.scraper_controller.load_data()
            if not self.speaker_collection.speakers:
                st.warning("No speaker data found. Please run the scraper first.")
                return False
            return True
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return False
    
    async def run_scraper(self):
        """Run the scraper to collect speaker data."""
        try:
            with st.spinner("Scraping speaker data... This may take a few minutes."):
                self.speaker_collection = await run_scraper()
            
            if self.speaker_collection and self.speaker_collection.speakers:
                st.success(f"Successfully scraped {len(self.speaker_collection.speakers)} speakers!")
                return True
            else:
                st.error("No speakers were scraped. Please check the logs for details.")
                return False
        except Exception as e:
            st.error(f"Error running scraper: {e}")
            return False
    
    def display_speaker_list(self):
        """Display the list of speakers."""
        if not self.speaker_collection or not self.speaker_collection.speakers:
            return
        
        st.subheader("All Speakers")
        
        # Convert to DataFrame for easier display
        speakers_df = pd.DataFrame([s.to_dict() for s in self.speaker_collection.speakers])
        
        # Add a column for the speaker index
        speakers_df.insert(0, "#", range(1, len(speakers_df) + 1))
        
        # Display the DataFrame
        st.dataframe(
            speakers_df,
            column_config={
                "#": st.column_config.NumberColumn(
                    "Index",
                    help="Speaker index",
                    width="small",
                ),
                "name": st.column_config.TextColumn(
                    "Name",
                    help="Speaker name",
                    width="medium",
                ),
                "position": st.column_config.TextColumn(
                    "Position",
                    help="Speaker position",
                    width="medium",
                ),
                "company": st.column_config.TextColumn(
                    "Company",
                    help="Speaker company",
                    width="medium",
                ),
                "description": st.column_config.TextColumn(
                    "Description",
                    help="Speaker description",
                    width="large",
                ),
                "session_title": st.column_config.TextColumn(
                    "Session Title",
                    help="Session title",
                    width="large",
                ),
                "date": st.column_config.TextColumn(
                    "Date",
                    help="Session date",
                    width="small",
                ),
                "time": st.column_config.TextColumn(
                    "Time",
                    help="Session time",
                    width="small",
                ),
                "location": st.column_config.TextColumn(
                    "Location",
                    help="Session location",
                    width="small",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
    
    def display_speaker_details(self, speaker: Speaker):
        """
        Display detailed information for a speaker.
        
        Args:
            speaker: The Speaker object to display
        """
        st.subheader(speaker.name)
        
        # Create columns for layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"**Position:** {speaker.position}")
            st.markdown(f"**Company:** {speaker.company}")
            
            if speaker.date != "Not available":
                st.markdown(f"**Date:** {speaker.date}")
            
            if speaker.time != "Not available":
                st.markdown(f"**Time:** {speaker.time}")
            
            if speaker.location != "Not available":
                st.markdown(f"**Location:** {speaker.location}")
        
        with col2:
            if speaker.session_title != "Not available":
                st.markdown(f"**Session Title:** {speaker.session_title}")
            
            if speaker.description != "No description available":
                st.markdown("**Description:**")
                st.markdown(speaker.description)
    
    def display_statistics(self):
        """Display statistics about the speaker data."""
        if not self.speaker_collection or not self.speaker_collection.speakers:
            return
        
        st.subheader("Statistics")
        
        # Create columns for layout
        col1, col2 = st.columns(2)
        
        # Convert to DataFrame for easier analysis
        speakers_df = pd.DataFrame([s.to_dict() for s in self.speaker_collection.speakers])
        
        with col1:
            # Company statistics
            st.markdown("### Top Companies")
            company_counts = speakers_df['company'].value_counts().reset_index()
            company_counts.columns = ['Company', 'Count']
            company_counts = company_counts[company_counts['Company'] != 'Unknown']
            # Sort in descending order and take top 10
            company_counts = company_counts.sort_values('Count', ascending=False).head(10)
            
            fig = px.bar(
                company_counts,
                x='Count',
                y='Company',
                orientation='h',
                title='Top 10 Companies',
                labels={'Count': 'Number of Speakers', 'Company': ''},
                height=400,
            )
            # Ensure x-axis shows integers only
            fig.update_xaxes(tickmode='linear', dtick=1)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Date statistics
            st.markdown("### Speakers by Date")
            
            # Filter out 'Not available' dates
            date_df = speakers_df[speakers_df['date'] != 'Not available']
            
            if not date_df.empty:
                date_counts = date_df['date'].value_counts().reset_index()
                date_counts.columns = ['Date', 'Count']
                
                fig = px.pie(
                    date_counts,
                    values='Count',
                    names='Date',
                    title='Speakers by Date',
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No date information available for speakers.")
        
        # Location statistics
        st.markdown("### Speakers by Location")
        location_df = speakers_df[speakers_df['location'] != 'Not available']
        
        if not location_df.empty:
            location_counts = location_df['location'].value_counts().reset_index()
            location_counts.columns = ['Location', 'Count']
            
            fig = px.bar(
                location_counts,
                x='Location',
                y='Count',
                title='Speakers by Location',
                labels={'Count': 'Number of Speakers', 'Location': ''},
                height=400,
            )
            # Ensure y-axis shows integers only
            fig.update_yaxes(tickmode='linear', dtick=1)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No location information available for speakers.")
    
    def display_search(self):
        """Display search functionality."""
        if not self.speaker_collection or not self.speaker_collection.speakers:
            return
        
        st.subheader("Search Speakers")
        
        # Create columns for search inputs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_name = st.text_input("Search by Name")
        
        with col2:
            search_company = st.text_input("Search by Company")
        
        with col3:
            search_date = st.text_input("Search by Date")
        
        # Perform search
        if search_name or search_company or search_date:
            results = []
            
            for speaker in self.speaker_collection.speakers:
                if (search_name.lower() in speaker.name.lower() and
                    search_company.lower() in speaker.company.lower() and
                    search_date.lower() in speaker.date.lower()):
                    results.append(speaker)
            
            if results:
                st.success(f"Found {len(results)} matching speakers")
                
                # Convert to DataFrame for display
                results_df = pd.DataFrame([s.to_dict() for s in results])
                
                # Display results
                st.dataframe(
                    results_df,
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.warning("No matching speakers found")
    
    def display_export_options(self):
        """Display export options."""
        if not self.speaker_collection or not self.speaker_collection.speakers:
            return
        
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export to JSON"):
                # Data is already saved to JSON during scraping
                st.success(f"Data exported to {config.OUTPUT_JSON_FILE}")
                st.markdown(f"Download from: `{config.OUTPUT_JSON_FILE}`")
        
        with col2:
            if st.button("Export to CSV"):
                # Data is already saved to CSV during scraping
                st.success(f"Data exported to {config.OUTPUT_CSV_FILE}")
                st.markdown(f"Download from: `{config.OUTPUT_CSV_FILE}`")
    
    def get_last_updated_time(self):
        """Get the last updated time of the data files."""
        try:
            if os.path.exists(config.OUTPUT_JSON_FILE):
                mod_time = os.path.getmtime(config.OUTPUT_JSON_FILE)
                return datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def run(self):
        """Run the Streamlit application."""
        # Sidebar controls
        st.sidebar.subheader("Data Collection")
        
        # Display last updated time
        last_updated = self.get_last_updated_time()
        st.sidebar.info(f"Data last updated: {last_updated}")
        
        # Admin section (hidden by default)
        with st.sidebar.expander("Admin Options", expanded=False):
            st.warning("⚠️ Running the scraper directly from Streamlit Cloud may not work due to IP blocking and other limitations.")
            if st.button("Run Scraper (Admin Only)"):
                asyncio.run(self.run_scraper())
        
        if st.sidebar.button("Load Data"):
            self.load_data()
        
        # Always try to load data automatically
        if not self.speaker_collection:
            self.load_data()
        
        # If data is loaded, display it
        if self.speaker_collection and self.speaker_collection.speakers:
            # Sidebar navigation
            st.sidebar.subheader("Navigation")
            page = st.sidebar.radio(
                "Go to",
                ["Speaker List", "Statistics", "Search", "Export"]
            )
            
            # Display the selected page
            if page == "Speaker List":
                self.display_speaker_list()
            elif page == "Statistics":
                self.display_statistics()
            elif page == "Search":
                self.display_search()
            elif page == "Export":
                self.display_export_options()
        else:
            # No data loaded, display welcome message
            st.markdown("""
            ## Welcome to the World Retail Congress Speakers Scraper
            
            This application allows you to analyze speaker data from the World Retail Congress website.
            
            The data is automatically updated daily via GitHub Actions. You can see when the data was last updated in the sidebar.
            
            If the data doesn't load automatically, click the "Load Data" button in the sidebar.
            """)


def main():
    """Main function to run the Streamlit application."""
    view = StreamlitView()
    view.run()


if __name__ == "__main__":
    main()