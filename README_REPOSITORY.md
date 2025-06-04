# 🔬 Medical Spytool v1.3-beta

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Beta-orange.svg)](RELEASE_NOTES_v1.2-beta.md)

**Professional Medical Literature Research Tool for German National Library (DNB) and PubMed**

---

## 🎯 Overview

Medical Spytool v1.3-beta is a comprehensive research tool designed for medical professionals, researchers, and students to efficiently search and analyze medical literature from:

- **German National Library (DNB)** - Complete German medical literature database
- **PubMed** - International medical literature database
- **Combined searches** - Comprehensive multi-database research

### ✨ Key Features

- **🔍 Advanced Search Capabilities** - Search by author, title, keyword, or complex queries
- **📊 Analytics & Visualization** - Generate publication statistics and trend analysis  
- **📈 Export Functions** - CSV, Excel, JSON, and PDF report generation
- **🖥️ Modern GUI Interface** - User-friendly graphical interface
- **⚡ CLI Support** - Command-line interface for automation
- **🎨 Clean Data Display** - Professional output without clutter (no "N/A" values)

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/[username]/medical-spytool.git
cd medical-spytool
pip install -r requirements.txt
```

### GUI Usage (Recommended)

```bash
python -m dnb_spytool --gui
```

### CLI Usage

```bash
# Search single author
python -m dnb_spytool --author "Robert Koch"

# Search multiple authors with export
python -m dnb_spytool --authors "Koch,Virchow,Ehrlich" --format excel --output medical_research.xlsx

# Generate analytics report
python -m dnb_spytool --author "Alexander Fleming" --analytics --report-format pdf
```

---

## 📋 What's New in v1.3-beta

### 🔧 Phase 1 Fixes (Completed)
- ✅ **Eliminated "N/A" Values** - Clean, professional data display
- ✅ **Enhanced MARC Parser** - Improved data extraction robustness
- ✅ **Better Author Recognition** - Support for corporate authors and duplicates removal
- ✅ **Improved Field Validation** - Better ISBN/ISSN validation and language detection
- ✅ **Consistent Distribution** - All versions (Source, Portable, Main) synchronized

### 🎯 Key Improvements
- **Robust Data Extraction** - Enhanced MARC record parsing for titles, authors, ISBNs
- **Clean GUI Display** - No more "N/A" clutter in the interface
- **Better Error Handling** - Graceful handling of missing or incomplete data
- **Enhanced Analytics** - More comprehensive publication analysis

---

## 📁 Project Structure

```
medical-spytool/
├── dnb_spytool/           # Main application package
│   ├── api/               # API clients and parsers
│   ├── gui/               # Graphical user interface
│   ├── analytics/         # Analytics and visualization
│   └── utils/             # Utilities and exporters
├── FINAL_DISTRIBUTION/    # Ready-to-use distributions
│   ├── Source/            # Source distribution
│   ├── Portable-App/      # Portable application
│   └── Windows-Executable/ # Windows .exe version
├── tests/                 # Test suite
├── docs/                  # Documentation
└── examples/              # Usage examples
```

---

## 🛠️ Available Distributions

### 1. **Source Distribution** (Developers)
```bash
cd FINAL_DISTRIBUTION/Source
python -m dnb_spytool --gui
```

### 2. **Portable App** (End Users)
```bash
cd FINAL_DISTRIBUTION/Portable-App/Medical-Spytool-Portable
python -m dnb_spytool --gui
```

### 3. **Windows Executable** (Windows Users)
- Double-click `Medical_Spytool.exe` in `FINAL_DISTRIBUTION/Windows-Executable/`

---

## 📊 Usage Examples

### Medical Research Workflow

1. **Author Research**
   ```bash
   python -m dnb_spytool --author "Rudolf Virchow" --database both --analytics
   ```

2. **Historical Analysis**
   ```bash
   python -m dnb_spytool --authors "Koch,Pasteur,Lister" --format excel --output pioneers.xlsx
   ```

3. **Modern Research**
   ```bash
   python -m dnb_spytool --author "Anthony Fauci" --database pubmed --max-results 50
   ```

---

## 🔍 Search Capabilities

### Supported Databases
- **DNB (German National Library)** - German medical literature
- **PubMed** - International medical literature  
- **Both** - Combined searches for comprehensive research

### Search Types
- **Single Author** - `--author "Name"`
- **Multiple Authors** - `--authors "Name1,Name2,Name3"`
- **Advanced Queries** - Complex search patterns
- **Keyword Search** - Topic-based searches

### Export Formats
- **CSV** - Spreadsheet compatible
- **Excel** - Professional formatted tables
- **JSON** - Machine-readable data
- **PDF** - Analytics reports with visualizations

---

## 🧪 Testing & Verification

### Run Complete Test Suite
```bash
python test_complete_functionality.py
```

### Quick GUI Test
```bash
python -m dnb_spytool --gui
# Search for "Robert Koch" to verify functionality
```

### CLI Test
```bash
python -m dnb_spytool --author "Alexander Fleming" --max-results 5
```

---

## 📈 Analytics Features

- **Publication Timeline** - Chronological analysis of research output
- **Collaboration Networks** - Co-author analysis
- **Topic Trends** - Subject matter evolution over time
- **Database Comparison** - DNB vs PubMed coverage analysis
- **Statistical Reports** - Comprehensive research metrics

---

## 🔧 Development

### Requirements
- Python 3.8+
- tkinter (GUI)
- requests (API calls)
- matplotlib (Visualizations)
- pandas (Data processing)
- openpyxl (Excel export)

### Development Setup
```bash
git clone https://github.com/[username]/medical-spytool.git
cd medical-spytool
pip install -r requirements-dev.txt
python -m pytest tests/
```

---

## 📚 Documentation

- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[User Manual](docs/user_manual.md)** - Comprehensive usage guide
- **[API Documentation](docs/api.md)** - Developer reference
- **[Examples](examples/)** - Practical usage examples

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏆 Acknowledgments

- **German National Library (DNB)** - For providing comprehensive literature access
- **PubMed/NCBI** - For international medical literature database
- **Python Community** - For excellent libraries and tools
- **Medical Research Community** - For continuous feedback and requirements

---

## 📞 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Check the `docs/` folder for detailed guides
- **Examples**: See `examples/` for practical usage scenarios

---

**Medical Spytool v1.3-beta - Empowering Medical Research with Technology** 🔬
