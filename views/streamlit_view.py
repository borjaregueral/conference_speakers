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
import pytz

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
        
        # Simple CSS for better visualization - using light theme compatible styling
        st.markdown("""
        <style>
        /* Basic styling that works well with light theme */
        .stDataFrame {
            overflow-x: auto !important;
        }
        
        /* Ensure text is visible on light background */
        .dataframe {
            color: #333333 !important;
        }
        
        /* Make sure headers are visible */
        th {
            background-color: #f0f2f6 !important;
            color: #333333 !important;
        }
        
        /* Ensure row colors alternate properly */
        tr:nth-child(even) {
            background-color: #f9f9f9 !important;
        }
        
        tr:nth-child(odd) {
            background-color: #ffffff !important;
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
        
        # Create tabs for different views
        speaker_info_tab, session_info_tab = st.tabs(["Speaker Information", "Session Information"])
        
        with speaker_info_tab:
            st.markdown("### Speaker and Company Details")
            
            # Create a copy of the dataframe with renamed columns
            speaker_info_df = speakers_df.copy()
            
            # Rename columns to remove "company_" prefix
            column_mapping = {
                'company_type': 'type',
                'company_size': 'size',
                'company_hq_country': 'hq_country',
                'company_international': 'international'
            }
            
            speaker_info_df = speaker_info_df.rename(columns=column_mapping)
            
            # Select columns for display
            display_columns = [
                "name", "position", "company",
                "type", "size", "hq_country", "international"
            ]
            
            # Use the basic st.table for better light theme compatibility
            st.table(speaker_info_df[display_columns].reset_index(drop=True))
        
        with session_info_tab:
            st.markdown("### Session Details")
            
            # Create a copy of the dataframe with selected columns
            session_df = speakers_df[["name", "session_title", "description", "date", "time", "location"]].copy()
            
            # Truncate long descriptions to make the column narrower
            session_df['description'] = session_df['description'].str.slice(0, 100) + '...'
            
            # Create a new column combining date and time
            session_df['date_time'] = session_df['date'] + ' ' + session_df['time']
            
            # Select and reorder columns for display
            display_columns = ["name", "session_title", "description", "date_time", "location"]
            
            # Use a dataframe for better handling of sessions not assigned to speakers
            st.dataframe(
                session_df[display_columns],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "name": "Speaker",
                    "session_title": "Session Title",
                    "description": "Description",
                    "date_time": "Date & Time",
                    "location": "Location"
                }
            )
        
        # Add an expander for viewing all data if needed
        with st.expander("View Complete Data (All Columns)"):
            st.dataframe(
                speakers_df,
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
            
            # Display company enrichment data if available
            if speaker.company_type != "Not available":
                st.markdown(f"**Type:** {speaker.company_type}")
                
            if speaker.company_size != "Not available":
                st.markdown(f"**Size:** {speaker.company_size}")
                
            if speaker.company_hq_country != "Not available":
                st.markdown(f"**HQ Country:** {speaker.company_hq_country}")
                
            if speaker.company_international != "Not available":
                st.markdown(f"**International:** {speaker.company_international}")
            
            if speaker.date != "Not available":
                st.markdown(f"**Date:** {speaker.date}")
            
            if speaker.time != "Not available":
                st.markdown(f"**Time:** {speaker.time}")
            
            if speaker.location != "Not available":
                st.markdown(f"**Location:** {speaker.location}")
            
        
        with col2:
            if speaker.session_title != "Not available":
                st.markdown(f"**Session Title:** {speaker.session_title}")
            
            # Display company headquarters address if available
            if speaker.company_hq_address != "Not available":
                st.markdown("**Headquarters Address:**")
                st.markdown(speaker.company_hq_address)
            
            
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
        company_tab, size_tab, international_tab, date_tab, location_tab, time_tab, network_tab = st.tabs([
            "Companies", "Size", "International", "Dates", "Locations", "Time Slots", "Network Analysis"
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
                    title='Companies Representation',
                    height=400,
                    color='Count',
                    color_continuous_scale='Blues',
                )
                # Hide color bar/legend
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # No additional chart needed
        
        # ---- SIZE STATISTICS ----
        with size_tab:
            st.markdown("### Company Size Distribution")
            
            # Filter out 'Not available' sizes
            company_size_df = speakers_df[speakers_df['company_size'] != 'Not available'].copy()
            
            if not company_size_df.empty:
                # Count by size
                size_counts = company_size_df['company_size'].value_counts().reset_index()
                size_counts.columns = ['Size', 'Count']
                size_counts = size_counts.sort_values('Count', ascending=False)
                
                # Create an improved bar chart for sizes
                fig = px.bar(
                    size_counts,
                    x='Size',
                    y='Count',
                    title='Company Size Distribution',
                    labels={'Count': 'Number of Companies', 'Size': 'Company Size'},
                    height=500,
                    color='Count',
                    color_continuous_scale='Viridis',
                    text='Count',
                )
                fig.update_xaxes(tickangle=45, title_font=dict(size=14))
                fig.update_yaxes(title_font=dict(size=14))
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside', marker_line_width=1.5)
                fig.update_coloraxes(showscale=False)
                fig.update_layout(
                    title_font=dict(size=18),
                    bargap=0.2,
                    plot_bgcolor='rgba(240,240,240,0.2)'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No company size information available.")
            
            # Enrichment rate for size
            enriched_size_count = len(speakers_df[speakers_df['company_size'] != 'Not available'])
            total_count = len(speakers_df)
            enrichment_rate = (enriched_size_count / total_count) * 100 if total_count > 0 else 0
            
            st.markdown(f"""
            ### Size Enrichment Statistics
            - **Total Companies**: {total_count}
            - **Companies with Size Data**: {enriched_size_count}
            - **Enrichment Rate**: {enrichment_rate:.2f}%
            """)
            
            # Create a progress bar for enrichment rate
            st.progress(enrichment_rate / 100)
        
        # ---- INTERNATIONAL STATISTICS ----
        with international_tab:
            st.markdown("### International vs. Domestic Companies")
            
            # Create columns for different visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Count all international statuses including 'Not available'
                all_international_counts = speakers_df['company_international'].value_counts().reset_index()
                all_international_counts.columns = ['International', 'Count']
                
                # Create pie chart for all international statuses
                fig = px.pie(
                    all_international_counts,
                    values='Count',
                    names='International',
                    title='All International Statuses (Including Not Available)',
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Filter out 'Not available' international statuses
                international_df = speakers_df[speakers_df['company_international'] != 'Not available'].copy()
                
                if not international_df.empty:
                    # Count by international status
                    international_counts = international_df['company_international'].value_counts().reset_index()
                    international_counts.columns = ['International', 'Count']
                    
                    # Create pie chart for international statuses
                    fig = px.pie(
                        international_counts,
                        values='Count',
                        names='International',
                        title='Enriched International vs. Domestic Companies',
                        height=400,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No enriched international status information available.")
            
            # Enrichment rate for international status
            enriched_international_count = len(speakers_df[speakers_df['company_international'] != 'Not available'])
            total_count = len(speakers_df)
            enrichment_rate = (enriched_international_count / total_count) * 100 if total_count > 0 else 0
            
            st.markdown(f"""
            ### International Status Enrichment Statistics
            - **Total Companies**: {total_count}
            - **Companies with International Status Data**: {enriched_international_count}
            - **Enrichment Rate**: {enrichment_rate:.2f}%
            """)
            
            # Create a progress bar for enrichment rate
            st.progress(enrichment_rate / 100)
            
            # Company HQ Country Analysis
            st.markdown("### Headquarters by Country")
            
            # Filter out 'Not available' HQ countries
            hq_country_df = speakers_df[speakers_df['company_hq_country'] != 'Not available'].copy()
            
            if not hq_country_df.empty:
                # Count by HQ country
                country_counts = hq_country_df['company_hq_country'].value_counts().reset_index()
                country_counts.columns = ['Country', 'Count']
                country_counts = country_counts.sort_values('Count', ascending=False)
                
                # Create bar chart for HQ countries
                fig = px.bar(
                    country_counts,
                    x='Country',
                    y='Count',
                    title='Headquarters by Country',
                    labels={'Count': 'Number of Companies', 'Country': ''},
                    height=500,
                    color='Count',
                    color_continuous_scale='Blues',
                    text='Count',
                )
                fig.update_xaxes(tickangle=45)
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No headquarters information available.")
        
        # ---- DATE STATISTICS ----
        
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
                        color_continuous_scale='Blues',
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
                            background-color: rgba(100, 149, 237, {intensity/100});
                            padding: 10px;
                            border-radius: 5px;
                            margin-bottom: 10px;
                            display: flex;
                            justify-content: space-between;
                            color: #333333;
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
            
            location_df = speakers_df[speakers_df['location'] != 'Not available'].copy()
            
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
                        color_continuous_scale='Blues',
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
                    # Create a combined dataframe with date and location (explicit copy)
                    combined_df = speakers_df[
                        (speakers_df['date'] != 'Not available') &
                        (speakers_df['location'] != 'Not available')
                    ].copy()
                    
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
            
            # Filter out 'Not available' times and create an explicit copy
            time_df = speakers_df[speakers_df['time'] != 'Not available'].copy()
            
            if not time_df.empty:
                # Extract hour from time slot (assuming format like "12:10 - 12:50")
                time_df.loc[:, 'hour'] = time_df['time'].str.extract(r'(\d+):', expand=False).astype(float)
                
                # Count speakers by hour
                hour_counts = time_df.groupby('hour').size().reset_index()
                hour_counts.columns = ['Hour', 'Count']
                hour_counts = hour_counts.copy()  # Create explicit copy
                
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
                    # Create a combined dataframe with date and hour (explicit copy)
                    combined_df = time_df[time_df['date'] != 'Not available'].copy()
                    
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
                            color_continuous_scale='Blues',
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
                title='Companies Network (Bubble Size = Number of Speakers)',
                labels={'x': '', 'y': ''},
                height=500,
                color='Speakers',
                color_continuous_scale='Blues',
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
                stop_words = {'and', 'your', 'how', 'you', 'are', 'main', 'stage', 'why', 'build', 'customers','the', 'in', 'of', 'to','may','plcs', 'a', 'for', 'track','new','with','where', 'on', 'by', 'at', 'from', 'not'}
                
                # Extract words and count frequencies
                words = []
                for title in all_titles:
                    # Extract words, convert to lowercase, and remove non-alphanumeric characters
                    title_words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
                    # Filter out stop words
                    title_words = [word for word in title_words if word not in stop_words]
                    words.extend(title_words)
                
                word_counts = Counter(words).most_common(30)
                word_df = pd.DataFrame(word_counts, columns=['Word', 'Count']).copy()
                
                # Create a bar chart of word frequencies
                fig = px.bar(
                    word_df,
                    x='Word',
                    y='Count',
                    title='Most Common Words in Session Titles',
                    labels={'Count': 'Frequency', 'Word': ''},
                    height=500,
                    color='Count',
                    color_continuous_scale='Blues',
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
                    ["All Fields", "Name", "Company", "Position", "Session Title", "Description", "Location", "Date",
                     "Type", "Size", "HQ Country", "International"]
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
                            (speakers_df['date'].str.lower() == search_term.lower()) |
                            (speakers_df['company_type'].str.lower() == search_term.lower()) |
                            (speakers_df['company_size'].str.lower() == search_term.lower()) |
                            (speakers_df['company_hq_country'].str.lower() == search_term.lower()) |
                            (speakers_df['company_international'].str.lower() == search_term.lower())
                        ]
                    else:
                        results_df = speakers_df[
                            (speakers_df['name'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['company'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['position'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['session_title'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['description'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['location'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['date'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['company_type'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['company_size'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['company_hq_country'].str.lower().str.contains(search_term.lower(), na=False)) |
                            (speakers_df['company_international'].str.lower().str.contains(search_term.lower(), na=False))
                        ]
                else:
                    # Map the search field to the actual column name
                    field_mapping = {
                        "name": "name",
                        "company": "company",
                        "position": "position",
                        "session title": "session_title",
                        "description": "description",
                        "location": "location",
                        "date": "date",
                        "type": "company_type",
                        "size": "company_size",
                        "hq country": "company_hq_country",
                        "international": "company_international"
                    }
                    
                    field = field_mapping.get(search_field.lower(), search_field.lower().replace(" ", "_"))
                    
                    if search_exact:
                        results_df = speakers_df[speakers_df[field].str.lower() == search_term.lower()]
                    else:
                        results_df = speakers_df[speakers_df[field].str.lower().str.contains(search_term.lower(), na=False)]
                
                if not results_df.empty:
                    st.success(f"Found {len(results_df)} matching speakers")
                    
                    # Add a column for the speaker index
                    results_df.insert(0, "#", range(1, len(results_df) + 1))
                    
                    # Display results
                    # Create a copy with renamed columns
                    display_results = results_df.copy()
                    
                    # Rename columns to remove "company_" prefix
                    column_mapping = {
                        'company_type': 'type',
                        'company_size': 'size',
                        'company_hq_country': 'hq_country',
                        'company_international': 'international'
                    }
                    
                    display_results = display_results.rename(columns=column_mapping)
                    
                    # Create tabs for different views of search results
                    search_speaker_tab, search_session_tab = st.tabs(["Speaker Information", "Session Information"])
                    
                    with search_speaker_tab:
                        speaker_columns = [
                            "name", "position", "company",
                            "type", "size", "hq_country", "international"
                        ]
                        st.table(display_results[speaker_columns].reset_index(drop=True))
                    
                    with search_session_tab:
                        # Create a copy of the dataframe with selected columns
                        session_df = display_results[["name", "session_title", "description", "date", "time", "location"]].copy()
                        
                        # Truncate long descriptions to make the column narrower
                        session_df['description'] = session_df['description'].str.slice(0, 100) + '...'
                        
                        # Create a new column combining date and time
                        session_df['date_time'] = session_df['date'] + ' ' + session_df['time']
                        
                        # Select and reorder columns for display
                        display_columns = ["name", "session_title", "description", "date_time", "location"]
                        
                        # Use a dataframe for better handling of sessions not assigned to speakers
                        st.dataframe(
                            session_df[display_columns],
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "name": "Speaker",
                                "session_title": "Session Title",
                                "description": "Description",
                                "date_time": "Date & Time",
                                "location": "Location"
                            }
                        )
                    
                    # Add an expander for viewing all data if needed
                    with st.expander("View Complete Search Results (All Columns)"):
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
            
            # Create three columns for more filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Get unique dates and locations for filtering
                unique_dates = sorted(speakers_df['date'].unique())
                unique_dates = [d for d in unique_dates if d != "Not available"]
                
                filter_dates = st.multiselect("Filter by Date", unique_dates)
            
            with col2:
                unique_locations = sorted(speakers_df['location'].unique())
                unique_locations = [l for l in unique_locations if l != "Not available"]
                
                filter_locations = st.multiselect("Filter by Location", unique_locations)
            
            with col3:
                # Add filters for enriched fields
                unique_company_types = sorted(speakers_df['company_type'].unique())
                unique_company_types = [t for t in unique_company_types if t != "Not available"]
                
                filter_company_types = st.multiselect("Filter by Type", unique_company_types)
            
            # Add more filters in a second row
            col4, col5, col6 = st.columns(3)
            
            with col4:
                unique_company_sizes = sorted(speakers_df['company_size'].unique())
                unique_company_sizes = [s for s in unique_company_sizes if s != "Not available"]
                
                filter_company_sizes = st.multiselect("Filter by Size", unique_company_sizes)
            
            with col5:
                unique_countries = sorted(speakers_df['company_hq_country'].unique())
                unique_countries = [c for c in unique_countries if c != "Not available"]
                
                filter_countries = st.multiselect("Filter by HQ Country", unique_countries)
            
            with col6:
                unique_international = sorted(speakers_df['company_international'].unique())
                unique_international = [i for i in unique_international if i != "Not available"]
                
                filter_international = st.multiselect("Filter by International", unique_international)
            
            # Apply filters
            filtered_df = speakers_df.copy()
            
            if filter_dates:
                filtered_df = filtered_df[filtered_df['date'].isin(filter_dates)]
            
            if filter_locations:
                filtered_df = filtered_df[filtered_df['location'].isin(filter_locations)]
            
            if filter_company_types:
                filtered_df = filtered_df[filtered_df['company_type'].isin(filter_company_types)]
            
            if filter_company_sizes:
                filtered_df = filtered_df[filtered_df['company_size'].isin(filter_company_sizes)]
            
            if filter_countries:
                filtered_df = filtered_df[filtered_df['company_hq_country'].isin(filter_countries)]
            
            if filter_international:
                filtered_df = filtered_df[filtered_df['company_international'].isin(filter_international)]
            
            # Display filtered results
            if filter_dates or filter_locations or filter_company_types or filter_company_sizes or filter_countries or filter_international:
                if not filtered_df.empty:
                    st.success(f"Found {len(filtered_df)} speakers matching your filters")
                    
                    # Add a column for the speaker index
                    filtered_df.insert(0, "#", range(1, len(filtered_df) + 1))
                    
                    # Display results
                    # Create a copy with renamed columns
                    display_filtered = filtered_df.copy()
                    
                    # Rename columns to remove "company_" prefix
                    column_mapping = {
                        'company_type': 'type',
                        'company_size': 'size',
                        'company_hq_country': 'hq_country',
                        'company_international': 'international'
                    }
                    
                    display_filtered = display_filtered.rename(columns=column_mapping)
                    
                    # Create tabs for different views of filtered results
                    filter_speaker_tab, filter_session_tab = st.tabs(["Speaker Information", "Session Information"])
                    
                    with filter_speaker_tab:
                        speaker_columns = [
                            "name", "position", "company",
                            "type", "size", "hq_country", "international"
                        ]
                        st.table(display_filtered[speaker_columns].reset_index(drop=True))
                    
                    with filter_session_tab:
                        # Create a copy of the dataframe with selected columns
                        session_df = display_filtered[["name", "session_title", "description", "date", "time", "location"]].copy()
                        
                        # Truncate long descriptions to make the column narrower
                        session_df['description'] = session_df['description'].str.slice(0, 100) + '...'
                        
                        # Create a new column combining date and time
                        session_df['date_time'] = session_df['date'] + ' ' + session_df['time']
                        
                        # Select and reorder columns for display
                        display_columns = ["name", "session_title", "description", "date_time", "location"]
                        
                        # Use a dataframe for better handling of sessions not assigned to speakers
                        st.dataframe(
                            session_df[display_columns],
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "name": "Speaker",
                                "session_title": "Session Title",
                                "description": "Description",
                                "date_time": "Date & Time",
                                "location": "Location"
                            }
                        )
                    
                    # Add an expander for viewing all data if needed
                    with st.expander("View Complete Filtered Results (All Columns)"):
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
                # Convert to CET timezone
                local_time = datetime.fromtimestamp(mod_time)
                cet_timezone = pytz.timezone('Europe/Paris')  # Paris is in CET/CEST
                local_timezone = datetime.now().astimezone().tzinfo
                local_time_with_tz = local_time.replace(tzinfo=local_timezone)
                cet_time = local_time_with_tz.astimezone(cet_timezone)
                return cet_time.strftime("%Y-%m-%d %H:%M:%S CET")
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def run(self):
        """Run the Streamlit application."""
        # Sidebar controls
        st.sidebar.subheader("Data Collection")
        # Display last updated time with custom styling
        last_updated = self.get_last_updated_time()
        st.sidebar.markdown(
            f"""
            <div style="
                background-color: rgba(100, 149, 237, 0.2);
                padding: 10px;
                border-radius: 5px;
                color: #333333;
                margin-bottom: 20px;
            ">
                <strong>Data last updated:</strong><br/>
                {last_updated}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        
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