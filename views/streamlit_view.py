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
            initial_sidebar_state="auto",  # Auto-collapse on mobile
            menu_items={
                'Get Help': 'https://github.com/borjaregueral/conference_speakers',
                'Report a bug': 'https://github.com/borjaregueral/conference_speakers/issues',
                'About': 'World Retail Congress Speakers Analyzer - Data updated daily via GitHub Actions'
            }
        )
        
        # Custom CSS for dark theme and better mobile experience
        st.markdown("""
        <style>
        /* Dark theme colors */
        :root {
            --primary-color: #4CAF50;
            --background-color: #121212;
            --secondary-background-color: #1e1e1e;
            --text-color: #f0f2f6;
            --font: 'Roboto', sans-serif;
        }
        
        /* Apply dark theme */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        
        .stSidebar {
            background-color: var(--secondary-background-color);
        }
        
        /* Style dataframes for dark theme */
        .stDataFrame {
            background-color: var(--secondary-background-color);
            border-radius: 5px;
        }
        
        /* Style buttons */
        .stButton button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            background-color: #388E3C;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Style tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: var(--secondary-background-color);
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
            border: none;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--primary-color);
            color: white;
        }
        
        /* Make the app more mobile-friendly */
        @media (max-width: 768px) {
            .stApp {
                padding: 0.5rem !important;
            }
            
            /* Adjust font sizes for mobile */
            h1 {
                font-size: 1.5rem !important;
            }
            h2 {
                font-size: 1.3rem !important;
            }
            h3 {
                font-size: 1.1rem !important;
            }
            
            /* Make dataframes scroll horizontally on mobile */
            .stDataFrame {
                overflow-x: auto !important;
            }
            
            /* Adjust chart sizes for mobile */
            .js-plotly-plot {
                max-height: 300px !important;
            }
        }
        
        /* Style charts for dark theme */
        .js-plotly-plot {
            background-color: var(--secondary-background-color);
            border-radius: 5px;
            padding: 10px;
        }
        
        /* Style text elements */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color);
        }
        
        /* Style info, success, warning boxes */
        .stAlert {
            border-radius: 4px;
        }
        </style>
        """, unsafe_allow_html=True)
        
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
        """Display enhanced statistics with multiple visualization types."""
        if not self.speaker_collection or not self.speaker_collection.speakers:
            return
        
        st.subheader("Statistics & Visualizations")
        
        # Convert to DataFrame for easier analysis
        speakers_df = pd.DataFrame([s.to_dict() for s in self.speaker_collection.speakers])
        
        # Create tabs for different visualization categories
        company_tab, date_tab, location_tab, time_tab, network_tab = st.tabs([
            "Companies", "Dates", "Locations", "Time Slots", "Network Analysis"
        ])
        
        # ---- COMPANY STATISTICS ----
        with company_tab:
            st.markdown("### Company Statistics")
            
            # Create columns for different visualizations
            col1, col2 = st.columns(2)
            
            # Prepare company data
            company_counts = speakers_df['company'].value_counts().reset_index()
            company_counts.columns = ['Company', 'Count']
            company_counts = company_counts[company_counts['Company'] != 'Unknown']
            company_counts = company_counts.sort_values('Count', ascending=False)
            
            with col1:
                # Horizontal bar chart for all companies with more than 1 speaker
                top_companies = company_counts[company_counts['Count'] > 1]
                
                fig = px.bar(
                    top_companies,
                    x='Count',
                    y='Company',
                    orientation='h',
                    title='Companies with more than one representative',
                    labels={'Count': 'Number of Speakers', 'Company': ''},
                    height=400,
                    color='Count',
                    color_continuous_scale='Blues',
                    text='Count',  # Add count as text on bars
                )
                # Hide x-axis ticks and numbers, keep title
                fig.update_xaxes(showticklabels=False, showgrid=False, title_text='Number of Speakers')
                # Keep y-axis labels (company names)
                fig.update_yaxes(showticklabels=True, showgrid=False)
                # Format the text on the bars - no decimals
                fig.update_traces(texttemplate='%{text:.0f}', textposition='inside')
                # Hide color bar/legend
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Treemap for company representation
                fig = px.treemap(
                    top_companies,
                    path=['Company'],
                    values='Count',
                    title='Company Representation',
                    height=400,
                    color='Count',
                    color_continuous_scale='Blues',
                )
                # Hide color bar/legend
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # No additional chart needed
        
        # ---- DATE STATISTICS ----
        with date_tab:
            st.markdown("### Date Statistics")
            
            # Filter out 'Not available' dates
            date_df = speakers_df[speakers_df['date'] != 'Not available']
            
            if not date_df.empty:
                # Create columns for different visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart for date distribution
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
                
                with col2:
                    # Bar chart for date comparison
                    fig = px.bar(
                        date_counts,
                        x='Date',
                        y='Count',
                        title='Speakers per Day',
                        labels={'Count': 'Number of Speakers', 'Date': ''},
                        height=400,
                        color='Count',
                        color_continuous_scale='Greens',
                        text='Count',  # Add count as text on bars
                    )
                    # Hide y-axis ticks and numbers, keep title
                    fig.update_yaxes(showticklabels=False, showgrid=False, title_text='Number of Speakers')
                    # Keep x-axis labels (dates)
                    fig.update_xaxes(showgrid=False)
                    # Format the text on the bars - no decimals
                    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                    # Hide color bar/legend
                    fig.update_coloraxes(showscale=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Calendar heatmap-style visualization
                st.markdown("### Daily Speaker Distribution")
                
                # Create a more visual representation of the schedule
                dates = sorted(date_counts['Date'].unique())
                
                # Create a simple calendar-like visualization
                for date in dates:
                    count = date_counts[date_counts['Date'] == date]['Count'].values[0]
                    intensity = min(count / max(date_counts['Count']) * 100, 100)
                    
                    st.markdown(
                        f"""
                        <div style="
                            background-color: rgba(76, 175, 80, {intensity/100});
                            padding: 10px;
                            border-radius: 5px;
                            margin-bottom: 10px;
                            display: flex;
                            justify-content: space-between;
                        ">
                            <span style="font-weight: bold;">{date}</span>
                            <span>{count} speakers</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("No date information available for speakers.")
        
        # ---- LOCATION STATISTICS ----
        with location_tab:
            st.markdown("### Location Statistics")
            
            location_df = speakers_df[speakers_df['location'] != 'Not available']
            
            if not location_df.empty:
                # Create columns for different visualizations
                col1, col2 = st.columns(2)
                
                # Prepare location data
                location_counts = location_df['location'].value_counts().reset_index()
                location_counts.columns = ['Location', 'Count']
                
                with col1:
                    # Bar chart for locations
                    fig = px.bar(
                        location_counts,
                        x='Location',
                        y='Count',
                        title='Speakers by Location',
                        labels={'Count': 'Number of Speakers', 'Location': ''},
                        height=400,
                        color='Count',
                        color_continuous_scale='Reds',
                        text='Count',  # Add count as text on bars
                    )
                    # Hide y-axis ticks and numbers, keep title
                    fig.update_yaxes(showticklabels=False, showgrid=False, title_text='Number of Speakers')
                    # Keep x-axis labels (locations)
                    fig.update_xaxes(showgrid=False)
                    # Format the text on the bars - no decimals
                    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                    # Hide color bar/legend
                    fig.update_coloraxes(showscale=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Pie chart for location distribution
                    fig = px.pie(
                        location_counts,
                        values='Count',
                        names='Location',
                        title='Location Distribution',
                        height=400,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Sunburst chart combining date and location
                if not date_df.empty:
                    # Create a combined dataframe with date and location
                    combined_df = speakers_df[
                        (speakers_df['date'] != 'Not available') &
                        (speakers_df['location'] != 'Not available')
                    ]
                    
                    if not combined_df.empty:
                        # Count speakers by date and location
                        combined_counts = combined_df.groupby(['date', 'location']).size().reset_index()
                        combined_counts.columns = ['Date', 'Location', 'Count']
                        
                        fig = px.sunburst(
                            combined_counts,
                            path=['Date', 'Location'],
                            values='Count',
                            title='Speakers by Date and Location',
                            height=600,
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No location information available for speakers.")
        
        # ---- TIME SLOT STATISTICS ----
        with time_tab:
            st.markdown("### Time Slot Analysis")
            
            # Filter out 'Not available' times
            time_df = speakers_df[speakers_df['time'] != 'Not available']
            
            if not time_df.empty:
                # Extract hour from time slot (assuming format like "12:10 - 12:50")
                time_df['hour'] = time_df['time'].str.extract(r'(\d+):', expand=False).astype(float)
                
                # Count speakers by hour
                hour_counts = time_df.groupby('hour').size().reset_index()
                hour_counts.columns = ['Hour', 'Count']
                
                # Sort by hour
                hour_counts = hour_counts.sort_values('Hour')
                
                # Create a line chart for time distribution
                fig = px.line(
                    hour_counts,
                    x='Hour',
                    y='Count',
                    title='Speakers by Hour of Day',
                    labels={'Count': 'Number of Speakers', 'Hour': 'Hour of Day'},
                    height=400,
                    markers=True,
                    text='Count',  # Add count as text on points
                )
                # Ensure y-axis shows integers only and remove grid
                fig.update_yaxes(showticklabels=False, showgrid=False)
                # Remove x-axis grid
                fig.update_xaxes(showgrid=False)
                # Format the text on the points - no decimals
                fig.update_traces(texttemplate='%{text:.0f}', textposition='top center')
                # Update color bar to show integers only
                fig.update_coloraxes(colorbar_tickformat='.0f')
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a heatmap-style visualization of the daily schedule
                if not date_df.empty:
                    # Create a combined dataframe with date and hour
                    combined_df = time_df[time_df['date'] != 'Not available']
                    
                    if not combined_df.empty:
                        # Count speakers by date and hour
                        schedule_counts = combined_df.groupby(['date', 'hour']).size().reset_index()
                        schedule_counts.columns = ['Date', 'Hour', 'Count']
                        
                        # Create a pivot table for the heatmap
                        schedule_pivot = schedule_counts.pivot(index='Date', columns='Hour', values='Count').fillna(0)
                        
                        fig = px.imshow(
                            schedule_pivot,
                            title='Conference Schedule Heatmap',
                            labels=dict(x='Hour of Day', y='Date', color='Number of Speakers'),
                            height=400,
                            color_continuous_scale='Viridis',
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No time information available for speakers.")
        
        # ---- NETWORK ANALYSIS ----
        with network_tab:
            st.markdown("### Network Analysis")
            
            # Create a simple network visualization of companies and their speakers
            company_speaker_counts = speakers_df.groupby('company')['name'].count().reset_index()
            company_speaker_counts.columns = ['Company', 'Speakers']
            company_speaker_counts = company_speaker_counts.sort_values('Speakers', ascending=False)
            
            # Take top companies for visualization
            top_companies = company_speaker_counts.head(15)
            
            # Create a network graph
            st.markdown("#### Top Companies and Their Speaker Count")
            
            # Create a bubble chart as a simple network visualization
            fig = px.scatter(
                top_companies,
                x=range(len(top_companies)),
                y=[1] * len(top_companies),
                size='Speakers',
                text='Company',
                title='Company Network (Bubble Size = Number of Speakers)',
                labels={'x': '', 'y': ''},
                height=500,
                color='Speakers',
                color_continuous_scale='Viridis',
            )
            
            # Remove axes and grid for cleaner look
            fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)
            fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False)
            
            # Adjust text position
            fig.update_traces(textposition='top center')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Word cloud-like visualization for session topics
            st.markdown("#### Common Words in Session Titles")
            
            # Extract words from session titles
            all_titles = speakers_df['session_title'].dropna().tolist()
            all_titles = [title for title in all_titles if title != 'Not available']
            
            if all_titles:
                # Simple word frequency analysis
                import re
                from collections import Counter
                
                # Common words to exclude
                stop_words = {'and', 'your', 'how', 'you', 'are', 'main', 'stage', 'why', 'build', 'customers','the', 'in', 'of', 'to','may','pics', 'a', 'for', 'track','new','with','where', 'on', 'by', 'at', 'from', 'not'}
                
                # Extract words and count frequencies
                words = []
                for title in all_titles:
                    # Extract words, convert to lowercase, and remove non-alphanumeric characters
                    title_words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
                    # Filter out stop words
                    title_words = [word for word in title_words if word not in stop_words]
                    words.extend(title_words)
                
                word_counts = Counter(words).most_common(30)
                word_df = pd.DataFrame(word_counts, columns=['Word', 'Count'])
                
                # Create a bar chart of word frequencies
                fig = px.bar(
                    word_df,
                    x='Word',
                    y='Count',
                    title='Most Common Words in Session Titles',
                    labels={'Count': 'Frequency', 'Word': ''},
                    height=500,
                    color='Count',
                    color_continuous_scale='Purples',
                    text='Count',  # Add count as text on bars
                )
                # Remove grid
                fig.update_yaxes(showgrid=False)
                fig.update_xaxes(showgrid=False)
                # Format the text on the bars - no decimals
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                # Update color bar to show integers only
                fig.update_coloraxes(colorbar_tickformat='.0f')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No session titles available for analysis.")
    
    def display_search(self):
        """Display enhanced search and filtering functionality."""
        if not self.speaker_collection or not self.speaker_collection.speakers:
            return
        
        st.subheader("Search & Filter Speakers")
        
        # Convert to DataFrame for easier filtering
        speakers_df = pd.DataFrame([s.to_dict() for s in self.speaker_collection.speakers])
        
        # Create tabs for different search/filter approaches
        search_tab, filter_tab = st.tabs(["Search", "Advanced Filters"])
        
        with search_tab:
            # Create columns for search inputs
            col1, col2 = st.columns(2)
            
            with col1:
                search_term = st.text_input("Search Term (searches across all fields)")
                search_exact = st.checkbox("Exact Match", value=False)
            
            with col2:
                search_field = st.selectbox(
                    "Search Field",
                    ["All Fields", "Name", "Company", "Position", "Session Title", "Description", "Location", "Date"]
                )
            
            # Perform search
            if search_term:
                if search_field == "All Fields":
                    if search_exact:
                        results_df = speakers_df[
                            (speakers_df['name'].str.lower() == search_term.lower()) |
                            (speakers_df['company'].str.lower() == search_term.lower()) |
                            (speakers_df['position'].str.lower() == search_term.lower()) |
                            (speakers_df['session_title'].str.lower() == search_term.lower()) |
                            (speakers_df['description'].str.lower() == search_term.lower()) |
                            (speakers_df['location'].str.lower() == search_term.lower()) |
                            (speakers_df['date'].str.lower() == search_term.lower())
                        ]
                    else:
                        results_df = speakers_df[
                            (speakers_df['name'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['company'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['position'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['session_title'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['description'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['location'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['date'].str.lower().str.contains(search_term.lower(), na=False))
                        ]
                else:
                    field = search_field.lower().replace(" ", "_")
                    if search_exact:
                        results_df = speakers_df[speakers_df[field].str.lower() == search_term.lower()]
                    else:
                        results_df = speakers_df[speakers_df[field].str.lower().str.contains(search_term.lower(), na=False)]
                
                if not results_df.empty:
                    st.success(f"Found {len(results_df)} matching speakers")
                    
                    # Add a column for the speaker index
                    results_df.insert(0, "#", range(1, len(results_df) + 1))
                    
                    # Display results
                    st.dataframe(
                        results_df,
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.warning("No matching speakers found")
        
        with filter_tab:
            # Create filter options
            st.markdown("### Filter Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Get unique dates and locations for filtering
                unique_dates = sorted(speakers_df['date'].unique())
                unique_dates = [d for d in unique_dates if d != "Not available"]
                
                filter_dates = st.multiselect("Filter by Date", unique_dates)
            
            with col2:
                unique_locations = sorted(speakers_df['location'].unique())
                unique_locations = [l for l in unique_locations if l != "Not available"]
                
                filter_locations = st.multiselect("Filter by Location", unique_locations)
            
            # Apply filters
            filtered_df = speakers_df.copy()
            
            if filter_dates:
                filtered_df = filtered_df[filtered_df['date'].isin(filter_dates)]
            
            if filter_locations:
                filtered_df = filtered_df[filtered_df['location'].isin(filter_locations)]
            
            # Display filtered results
            if filter_dates or filter_locations:
                if not filtered_df.empty:
                    st.success(f"Found {len(filtered_df)} speakers matching your filters")
                    
                    # Add a column for the speaker index
                    filtered_df.insert(0, "#", range(1, len(filtered_df) + 1))
                    
                    # Display results
                    st.dataframe(
                        filtered_df,
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.warning("No speakers match your filters")
    
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