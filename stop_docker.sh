#!/bin/bash

# Stop the World Retail Congress Speakers Scraper Docker container

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

# Stop the Docker container
echo "Stopping the Docker container..."
docker-compose down

echo "Docker container stopped successfully."