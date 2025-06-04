# Medical-Spytool User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Export Options](#export-options)
5. [Analytics](#analytics)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### First Launch
1. Start the application using your preferred method
2. The application will check for required dependencies
3. Missing packages will be installed automatically (with permission)

### Interface Options
- **GUI Mode**: `--gui` - User-friendly graphical interface
- **CLI Mode**: Default - Command-line interface for automation

## Basic Usage

### Searching for Authors

#### Single Author Search
```bash
# Basic search
Medical-Spytool --author "Johann Wolfgang von Goethe"

# With specific database
Medical-Spytool --author "Einstein" --database pubmed

# Limit results
Medical-Spytool --author "Kafka" --max-results 50
```

#### Multiple Authors
```bash
# Multiple authors at once
Medical-Spytool --authors "Goethe,Schiller,Heine"

# With output file
Medical-Spytool --authors "Darwin,Wallace" --output evolution_research.xlsx
```

### Database Selection
- **`dnb`** - German National Library (default)
- **`pubmed`** - PubMed/NCBI database
- **`both`** - Search both databases

### GUI Mode
1. Launch with `--gui`
2. Enter author names (one per line or comma-separated)
3. Select database and options
4. Click "Start Search"
5. Results appear in the table
6. Use "Export" to save results

## Advanced Features

### Batch Processing
Create a text file with author names (one per line):
```text
Johann Wolfgang von Goethe
Friedrich Schiller
Heinrich Heine
```

Run: `Medical-Spytool --authors-file authors.txt`

### Analytics Generation
```bash
# Generate analytics report
Medical-Spytool --author "Kafka" --analytics

# Choose report format
Medical-Spytool --author "Einstein" --analytics --report-format html

# Combined with search
Medical-Spytool --authors "Darwin,Wallace" --analytics --format xlsx
```

### Custom Output Paths
```bash
# Specific output file
Medical-Spytool --author "Goethe" --output "/path/to/results.csv"

# Custom format
Medical-Spytool --author "Schiller" --format json --output data.json
```

## Export Options

### Supported Formats
- **CSV** - Comma-separated values (default)
- **XLSX** - Excel format
- **JSON** - JavaScript Object Notation

### Data Fields
Each result includes:
- Title
- Author(s)
- Publication Year
- Publisher
- ISBN/DOI (if available)
- Abstract (if available)
- Database Source

### File Naming
Default naming pattern: `medical_spytool_results_YYYYMMDD_HHMMSS.format`

## Analytics

### Available Analytics
- **Publication Timeline** - Publications over time
- **Publisher Analysis** - Most frequent publishers
- **Collaboration Networks** - Co-author relationships
- **Subject Distribution** - Topic categories

### Report Formats
- **PDF** - Professional formatted report
- **HTML** - Interactive web report
- **Charts** - Individual chart images

## Troubleshooting

### Common Issues

**"Module not found" errors**
- Solution: Run with elevated permissions to install packages
- Alternative: Pre-install with `pip install -r requirements.txt`

**"Connection timeout"**
- Check internet connection
- Try again later (server may be busy)
- Use `--timeout 60` for longer timeout

**"No results found"**
- Check spelling of author names
- Try variations (with/without middle names)
- Try different databases

**"Permission denied" for output files**
- Choose a different output location
- Close the file if it's open in another program
- Run with appropriate permissions

### Performance Tips
- Use `--max-results` to limit large searches
- Enable verbose mode with `--verbose` for debugging
- Use specific databases instead of "both" for faster searches

### Getting Help
- Use `--help` for command-line options
- Check log files for detailed error information
- Consult the GitHub repository for updates

## Examples

See the Examples folder for:
- Basic usage scripts
- Batch processing examples
- Integration with other tools
- Custom export workflows
