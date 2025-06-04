# Medical-Spytool Windows Distribution

## Quick Start

### Option 1: Portable Application (Recommended)
1. Extract the ZIP file to any folder
2. Navigate to `Medical-Spytool-Portable`
3. Double-click `Medical-Spytool.bat` to start

### Option 2: Build Standalone Executable
1. Install Python 3.8+ from https://python.org
2. Open Command Prompt as Administrator
3. Navigate to the extracted folder
4. Run: `build_windows_exe.bat`
5. Find the executable in `dist/Medical-Spytool.exe`

### Option 3: Auto-py-to-exe (GUI Method)
1. Install: `pip install auto-py-to-exe`
2. Run: `auto-py-to-exe`
3. Load configuration: `auto-py-to-exe-config.json`
4. Click "Convert .py to .exe"

## Features

✅ **Medical Literature Search**
- German National Library (DNB) integration
- PubMed database support
- Advanced search filters

✅ **Data Export**
- Excel (XLSX) format
- CSV format
- JSON format

✅ **Analytics & Reporting**
- Publication statistics
- Author analysis
- Visual charts and graphs

✅ **User Interface**
- Command-line interface
- Graphical user interface (GUI)
- Batch processing support

## System Requirements

- **Operating System**: Windows 7, 8, 10, 11 (64-bit)
- **Python**: 3.8+ (for source version)
- **Memory**: 512 MB RAM minimum
- **Storage**: 100 MB free space
- **Internet**: Required for database searches

## Usage Examples

### Command Line
```cmd
# Search for a single author
Medical-Spytool.exe --author "Johann Wolfgang von Goethe"

# Search multiple authors with Excel output
Medical-Spytool.exe --authors "Goethe,Schiller" --format xlsx --output results.xlsx

# Generate analytics report
Medical-Spytool.exe --author "Kafka" --analytics --report-format pdf

# Launch GUI
Medical-Spytool.exe --gui
```

### Graphical Interface
1. Run `Medical-Spytool.exe --gui`
2. Enter author names in the search field
3. Select database (DNB, PubMed, or both)
4. Choose output format
5. Click "Start Search"

## Troubleshooting

### Common Issues

**"Missing Python libraries"**
- Solution: Use the portable version or install missing packages

**"Connection timeout"**
- Solution: Check internet connection and firewall settings

**"Access denied"**
- Solution: Run as Administrator or check antivirus settings

**"Slow performance"**
- Solution: Reduce maximum results or use filters

### Support

For technical support and bug reports:
- GitHub Issues: https://github.com/your-username/Medical-Spytool/issues
- Documentation: https://github.com/your-username/Medical-Spytool/wiki

## License

This software is distributed under the MIT License.
See LICENSE file for details.

## Acknowledgments

- German National Library (DNB) for API access
- PubMed/NCBI for research database
- Open source Python community

---
Medical-Spytool v1.0 - Professional Medical Literature Research Tool
