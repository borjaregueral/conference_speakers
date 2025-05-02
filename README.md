# World Retail Congress Speakers Scraper

This project scrapes speaker information from the [World Retail Congress 2025 Speakers page](https://www.worldretailcongress.com/2025-speakers) using Playwright for browser automation and provides a Streamlit UI for visualization and analysis.

## Features

- Automatically navigates to the World Retail Congress speakers page
- Accepts cookies consent
- Extracts detailed speaker information including:
  - Name
  - Position
  - Company
  - Description
  - Session title
  - Date
  - Time
  - Location
- Enriches company data using LLM with web search capabilities:
  - Company type/industry
  - Company size (number of employees)
  - Headquarters address
  - Headquarters country
  - International status
- Handles pagination to collect data from all pages
- Enriches company data every 10 speakers during scraping
- Saves speaker data to both JSON and CSV files
- Provides a Streamlit UI for visualization and analysis
- Dockerized for easy deployment

## Project Structure

The project follows an MVC (Model-View-Controller) architecture:

```
lead_conference/
├── models/                # Data models
│   ├── __init__.py
│   └── speaker.py         # Speaker data model
├── views/                 # UI views
│   ├── __init__.py
│   └── streamlit_view.py  # Streamlit UI
├── controllers/           # Business logic
│   ├── __init__.py
│   └── scraper_controller.py  # Scraper controller
├── utils/                 # Utility functions
│   ├── __init__.py
│   └── data_utils.py      # Data handling utilities
├── data/                  # Output data directory
│   ├── speakers.json      # JSON output file
│   └── speakers.csv       # CSV output file
├── app.py                 # Main application entry point
├── config.py              # Configuration settings
├── .env                   # Environment variables
├── .gitignore             # Git ignore file
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
├── run.sh                 # Script to run the application
├── run_scraper.sh         # Script to run just the scraper
├── test_enrichment.py     # Script to test company data enrichment
└── update_company_data.py # Script to update company data
```

## Requirements

- Python 3.9 or higher
- Playwright
- Streamlit
- Pandas
- Plotly
- Python-dotenv

## Installation

### Quick Setup

The easiest way to get started is to use the provided setup script:

```bash
# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This will install all required dependencies and set up Playwright.

### Manual Installation

If you prefer to install dependencies manually:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install
```

## Usage

### Running with Streamlit

```bash
# Make the run script executable
chmod +x run.sh

# Run the application
./run.sh
```

This will start the Streamlit application, which you can access at http://localhost:8501.

### Running the Scraper Only

To run just the scraper without the Streamlit UI:

```bash
# Make the script executable
chmod +x run_scraper.sh

# Run the scraper
./run_scraper.sh
```

### Utility Scripts

The project includes several utility scripts:

- **test_enrichment.py**: Tests the company data enrichment with a single speaker
  ```bash
  python test_enrichment.py
  ```

- **update_company_data.py**: Updates company data for all speakers or a sample
  ```bash
  # Update all speakers
  python update_company_data.py
  
  # Update a sample of 5 speakers
  python update_company_data.py sample
  ```

### Running with Docker

```bash
# Build and start the Docker container
docker-compose up -d

# View logs
docker-compose logs -f
```

This will start the Streamlit application in a Docker container, which you can access at http://localhost:8501.

## Streamlit UI

The Streamlit UI provides the following features:

- **Speaker List**: View all scraped speakers in a table
- **Statistics**: View statistics about the speakers, including:
  - Top companies
  - Speakers by date
  - Speakers by location
- **Search**: Search for speakers by name, company, or date
- **Export**: Export the data to JSON or CSV files

## Configuration

The application can be configured using the `config.py` file, which includes:

- URLs for scraping
- Output file paths
- Browser settings
- Scraper settings
- Streamlit settings
- OpenAI settings for company data enrichment

## Company Data Enrichment

The application uses OpenAI's GPT-4 Turbo model to enrich company information by searching the web. For each speaker's company, it collects:

- **Company Type/Industry**: The industry sector the company operates in (e.g., Retail, Technology, Finance)
- **Company Size**: Approximate number of employees
- **Headquarters Address**: Full address of the company's headquarters
- **Headquarters Country**: Country where the company is headquartered
- **International Status**: Whether the company has offices in multiple countries

The enrichment process is integrated into the scraping flow:

1. As speakers are scraped, they are added to a collection
2. Every 10 speakers (configurable via `SAVE_PROGRESS_INTERVAL`), the application:
   - Enriches company data for the newly scraped speakers
   - Saves the updated data to JSON and CSV files
3. This continues until all speakers are processed

This approach ensures that:
- Data is enriched incrementally during scraping
- Progress is saved regularly
- The application can be stopped and resumed without losing data

You can configure the enrichment process in the `.env` file:
- `ENABLE_COMPANY_ENRICHMENT`: Set to "true" to enable company data enrichment
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: The model to use for enrichment (default: "gpt-4-turbo")

## Docker

The application is dockerized for easy deployment. The Docker image includes:

- Python 3.10
- Playwright with Chromium
- All required dependencies
- The application code

## License

MIT