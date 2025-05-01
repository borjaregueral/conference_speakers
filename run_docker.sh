#!/bin/bash

# Run the World Retail Congress Speakers Scraper with Docker

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Build and start the Docker container
echo "Building and starting the Docker container..."
docker-compose up -d

# Print the URL
echo ""
echo "The application is now running at: http://localhost:9000"
echo ""
echo "To view the logs, run: docker-compose logs -f"
echo "To stop the application, run: docker-compose down"