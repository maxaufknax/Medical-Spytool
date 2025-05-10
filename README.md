# MedicalSpy - Scientific Publication Search Tool

MedicalSpy is a comprehensive web application for searching, analyzing, and managing scientific medical publications. It provides an intuitive interface for querying multiple scientific databases, managing researcher profiles, visualizing results, and exporting data in various formats.

![MedicalSpy Logo](generated-icon.png)

## Status

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker Support](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

## Features

- **Multi-Database Search**: Query PubMed and Deutsche Nationalbibliothek (DNB) with a unified interface
- **Researcher Management**: Maintain profiles of researchers and their publications
- **Advanced Search Options**: Filter by date range, language, publication type, and more
- **Result Visualization**: Generate charts and graphs of publication data
- **Data Export**: Export results to CSV, Excel, and other formats
- **Saved Searches**: Save and reuse complex search queries
- **Comprehensive Logging**: Track all activities and monitor system performance

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database
- System dependencies for Matplotlib (see below)

### System Dependencies

If you're using Linux, you may need these packages for Matplotlib and PostgreSQL:

```bash
# Debian/Ubuntu
sudo apt-get install libpq-dev python3-dev libfreetype6-dev pkg-config
```

### Setting Up a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r project_requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/medicalspy

# Session Secret - Change this to a random string in production!
SESSION_SECRET=your_secure_session_key_here

# API Keys
PUBMED_API_KEY=your_pubmed_api_key

# Logging Configuration
LOG_LEVEL=INFO

# Application Settings
OUTPUT_PATH=./output
PERSON_LIST_PATH=./person_lists
DEFAULT_DATABASE=PubMed
```

## Running the Application

### For Development

```bash
# Run with default settings
python run.py

# Run with custom port and host
python run.py --port 8080 --host 127.0.0.1

# Run with debug logging
python run.py --log-level DEBUG

# Check configuration without starting the server
python run.py --check-only
```

### Running Tests

The application includes a test suite that can be run with:

```bash
# Run all tests
python run_tests.py

# Run with increased verbosity
python run_tests.py -v
python run_tests.py -vv

# Run specific test file
python run_tests.py --test-path tests/test_config.py

# Run specific test directory
python run_tests.py --test-path tests/
```

### For Production

We recommend using Gunicorn as a WSGI server:

```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

For a more robust setup, consider using a reverse proxy like Nginx in front of Gunicorn.

### Using Docker

The application includes Docker and Docker Compose configurations for easy deployment:

```bash
# Build and start with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop containers
docker-compose down

# To retain database data between runs
docker-compose down
docker-compose up
```

### Database Management

The application includes database management tools:

```bash
# Check database connection
python db_tools.py --check

# Initialize database tables
python db_tools.py --init

# Reset database (drop and recreate all tables)
python db_tools.py --reset

# Add a sample person for testing
python db_tools.py --add-sample
```

## Database Schema

MedicalSpy uses SQLAlchemy with a PostgreSQL database. The main models are:

- **SearchQuery**: Stores saved search queries
- **SearchResult**: Stores results from search queries
- **Person**: Manages researcher profiles
- **Setting**: Stores application settings
- **LogEntry**: Tracks application logging

## API Connectors

The application includes connectors for different scientific databases:

- **PubMedConnector**: Connects to the PubMed E-utilities API
- **DNBConnector**: Connects to the Deutsche Nationalbibliothek SRU API

## Project Structure

```
medicalspy/
│
├── backend/           # Backend application code
│   ├── app.py         # Flask application setup
│   ├── models.py      # Database models
│   ├── connectors.py  # API connectors for databases
│   ├── search.py      # Search functionality
│   ├── utils.py       # Utility functions
│   ├── config.py      # Configuration management
│   ├── static/        # Static files (CSS, JS, images)
│   └── templates/     # HTML templates
│
├── logs/              # Application logs
├── output/            # Default directory for exported data
├── person_lists/      # Default directory for person lists
│
├── main.py            # Entry point for WSGI servers
├── run.py             # Development server with additional settings
├── .env               # Environment variables (not in version control)
├── .env.example       # Example environment variables
├── project_requirements.txt  # Python dependencies
└── README.md          # Project documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/my-new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- PubMed API from the National Center for Biotechnology Information (NCBI)
- Deutsche Nationalbibliothek (DNB) SRU Interface