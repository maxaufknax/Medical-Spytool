# Medical Spytool v1 - Usage Guide

## Quick Start

### GUI Mode (Recommended)
Double-click: `Start_Medical_Spytool_GUI.bat`

### Command Line Mode
Double-click: `Start_Medical_Spytool_CLI.bat`

## Command Line Examples

```cmd
# Search single author in both databases
Medical_Spytool.exe --author "Einstein, Albert" --database both

# Search with export
Medical_Spytool.exe --author "Darwin, Charles" --output results.csv

# Generate analytics
Medical_Spytool.exe --author "Watson, James" --analytics --format excel

# Show help
Medical_Spytool.exe --help
```

## Features
- Multi-database search (DNB + PubMed)
- Export to CSV, JSON, Excel, PDF
- Analytics and visualizations
- Real-time progress tracking

## System Requirements
- Windows 10/11
- Internet connection
- No additional software required

## Support
GitHub: https://github.com/maxaufknax/Medical-Spytool
