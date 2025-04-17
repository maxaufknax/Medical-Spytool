# MedicalSpy - Scientific Publication Search Tool

MedicalSpy is a comprehensive web-based application designed to search, analyze, and export scientific and medical publications from multiple databases including PubMed and the Deutsche Nationalbibliothek (DNB).

## Features

- **Multi-Database Search**: Search across PubMed and Deutsche Nationalbibliothek with a unified interface
- **Advanced Search Options**: Filter by date ranges, authors, publication types, and more
- **Person Management**: Associate searches with specific individuals for better organization
- **Result Visualization**: Analyze publication patterns with interactive charts
- **Data Export**: Export results to CSV or Excel formats for further analysis
- **Saved Queries**: Save and reuse common search queries
- **Detailed Logging**: Keep track of all search operations and system events

## Tech Stack

### Backend
- **Flask**: Web framework for the application
- **Requests**: For making HTTP requests to external databases
- **xml.etree.ElementTree**: For parsing XML responses from APIs
- **Pandas**: For data manipulation and export to Excel
- **Matplotlib**: For data visualization (server-side chart generation)

### Frontend
- **HTML5/CSS3**: For structure and styling
- **Bootstrap 5**: For responsive UI components
- **Vanilla JavaScript**: For client-side interactivity
- **Chart.js**: For interactive data visualizations

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
