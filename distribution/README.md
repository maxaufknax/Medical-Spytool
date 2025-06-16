# DNB Spytool v1.0.0 - Multi-Database Publication Search Tool

A comprehensive Python application for searching, retrieving, analyzing, and exporting publications from multiple academic databases including the German National Library (DNB) and PubMed.

## ✨ Features

- 🔍 **Multi-Database Search**: Search both German National Library (DNB) and PubMed databases
- 🎯 **Database Source Attribution**: Clear identification of publication sources with database breakdown
- 📊 **Advanced Analytics**: Comprehensive publication analysis with database-specific insights
- 💾 **Multiple Export Formats**: Save data to CSV, JSON, Excel, and PDF reports with source attribution
- 🖥️ **Dual Interface**: Modern GUI and powerful CLI interfaces
- 📈 **Rich Visualizations**: 6 chart types including database source distribution
- ⚡ **Real-time Progress**: Live search status with timing and database breakdown
- 🌐 **Cross-platform**: Compatible with Windows, macOS, and Linux

## 🚀 Quick Start

### Option 1: Use Portable Executable (Windows)
1. Download `DNB_Spytool_v1.0.0_Portable.zip`
2. Extract and run `Start_DNB_Spytool_GUI.bat` for GUI
3. Or run `Start_DNB_Spytool_CLI.bat` for command line

### Option 2: Install from Source
### Prerequisites
- Python 3.8 or higher
- pip package manager
- Internet connection for database access

### Install Dependencies

```bash
git clone https://github.com/yourusername/dnb-spytool.git
cd dnb-spytool
pip install -r requirements.txt
```

## 💻 Usage

### Multi-Database Search Examples

```bash
# Search both databases (recommended)
python -m dnb_spytool --author "Einstein, Albert" --database both --max-results 10

# Search specific database
python -m dnb_spytool --author "Darwin, Charles" --database dnb
python -m dnb_spytool --author "Watson, James" --database pubmed

# Multiple authors with analytics
python -m dnb_spytool --authors-file authors.txt --database both --analytics
```

### Command Line Interface (CLI)

```bash
# Single author search with export
python -m dnb_spytool --author "Johann Wolfgang von Goethe" --format csv --output results.csv

# Generate comprehensive analytics report
python -m dnb_spytool --author "Einstein, Albert" --database both --analytics --report-format pdf
```

### Graphical User Interface (GUI)

```bash
python -m dnb_spytool --gui
```

## API Integration

This tool uses the official DNB SRU (Search/Retrieve via URL) API:
- Base URL: `https://services.dnb.de/sru/dnb`
- Protocol: SRU 1.1
- Response Format: MARCXML

## Project Structure

```
dnb_spytool/
├── __init__.py
├── __main__.py              # Entry point for CLI
├── api/
│   ├── __init__.py
│   ├── dnb_client.py        # DNB API client
│   └── parser.py            # MARCXML parser
├── gui/
│   ├── __init__.py
│   ├── main_window.py       # Main GUI window
│   └── widgets.py           # Custom GUI widgets
├── analytics/
│   ├── __init__.py
│   ├── analyzer.py          # Data analysis functions
│   └── visualizer.py        # Chart generation
├── utils/
│   ├── __init__.py
│   ├── exporters.py         # Data export utilities
│   └── validators.py        # Input validation
└── cli.py                   # Command-line interface
```

## Screenshots

*Screenshots will be added after GUI implementation*

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

1. **Connection Error**: Check your internet connection and firewall settings
2. **No Results Found**: Verify author name spelling and try variations
3. **Export Error**: Ensure you have write permissions in the output directory

### Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review the API documentation at [DNB SRU API](https://www.dnb.de/EN/Professionell/Services/WissenschaftundForschung/SRU/sru_node.html)

## Acknowledgments

- German National Library (Deutsche Nationalbibliothek) for providing the SRU API
- Python community for excellent libraries and tools
