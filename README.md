# Medical Spytool

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-yellow)

**Medical Spytool** is a powerful Python application for searching and analyzing medical literature across multiple databases including PubMed, DNB (Deutsche Nationalbibliothek), and more.

## 🌟 Features

- **Multi-Database Search**: Search across PubMed, DNB, and other medical databases
- **Advanced Filtering**: Filter results by publication date, author, journal, and more
- **Export Capabilities**: Export results to JSON, CSV, Excel, and other formats
- **Batch Processing**: Process multiple search queries automatically
- **GUI Interface**: User-friendly graphical interface
- **CLI Support**: Command-line interface for automation
- **Data Visualization**: Generate charts and statistics from search results
- **API Integration**: RESTful API for external integrations

## 🚀 Quick Start

### Option 1: Download Executable (Recommended for Users)

1. Go to the [Releases](https://github.com/yourusername/Medical-Spytool/releases) page
2. Download the latest `Medical_Spytool.exe` for Windows
3. Run the executable - no installation required!

### Option 2: Python Installation (For Developers)

```bash
# Clone the repository
git clone https://github.com/yourusername/Medical-Spytool.git
cd Medical-Spytool

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Option 3: Development Setup

```bash
# Clone and setup for development
git clone https://github.com/yourusername/Medical-Spytool.git
cd Medical-Spytool

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Build executable
python scripts/build.py
```

## 📖 Usage

### GUI Mode

```bash
python src/main.py
```

This opens the graphical user interface where you can:
- Enter search terms
- Select databases to search
- Configure filters and options
- View and export results

### CLI Mode

```bash
# Basic search
python src/main.py --search "diabetes treatment" --database pubmed

# Advanced search with filters
python src/main.py --search "covid-19" --database pubmed,dnb --year-from 2020 --export results.json

# Batch processing
python src/main.py --batch queries.txt --output-dir results/
```

### API Usage

```python
from dnb_spytool import MedicalSpytool

# Initialize the tool
spytool = MedicalSpytool()

# Search PubMed
results = spytool.search_pubmed("diabetes treatment", max_results=100)

# Search multiple databases
results = spytool.search_multiple(["diabetes"], databases=["pubmed", "dnb"])

# Export results
spytool.export_results(results, "results.json", format="json")
```

## 📁 Project Structure

```
Medical-Spytool/
├── src/                    # Source code
│   ├── main.py            # Main application entry point
│   ├── gui/               # GUI components
│   └── cli/               # CLI components
├── dnb_spytool/           # Core library modules
│   ├── __init__.py
│   ├── search/            # Search engines
│   ├── export/            # Export functionality
│   └── utils/             # Utility functions
├── tests/                 # Test files
├── docs/                  # Documentation
├── examples/              # Usage examples
├── scripts/               # Build and utility scripts
└── distribution/          # Pre-built distributions
```

## 🔧 Configuration

Create a `config.json` file in the application directory:

```json
{
    "default_database": "pubmed",
    "max_results": 1000,
    "export_format": "json",
    "api_keys": {
        "pubmed": "your_api_key_here"
    }
}
```

## 📊 Supported Databases

- **PubMed**: Medical literature database
- **DNB**: Deutsche Nationalbibliothek
- **More databases**: Additional sources can be added via plugins

## 🔍 Search Examples

### Basic Searches
- `diabetes treatment`
- `covid-19 vaccines`
- `cancer immunotherapy`

### Advanced Searches
- `"machine learning" AND medicine`
- `author:"Smith J" AND year:2020-2023`
- `journal:"Nature" OR journal:"Science"`

## 📈 Export Formats

- JSON
- CSV
- Excel (XLSX)
- XML
- BibTeX
- RIS

## 🛠️ Development

### Requirements
- Python 3.8+
- tkinter (for GUI)
- requests
- pandas
- openpyxl
- beautifulsoup4

### Building from Source

```bash
# Install build dependencies
pip install pyinstaller

# Build executable
python scripts/build.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=medical_spytool --cov-report=html
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See the [docs/](docs/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/Medical-Spytool/issues)
- **Discussions**: Join discussions on [GitHub Discussions](https://github.com/yourusername/Medical-Spytool/discussions)

## 🏆 Acknowledgments

- Thanks to the PubMed and DNB teams for their APIs
- Built with Python and love for medical research
- Special thanks to all contributors

## 📊 Statistics

![GitHub Stats](https://github-readme-stats.vercel.app/api?username=yourusername&repo=Medical-Spytool&show_icons=true&theme=default)

---

**Made with ❤️ for medical researchers worldwide**
