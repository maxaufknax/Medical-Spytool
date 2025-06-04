# Installation Guide

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Memory**: Minimum 4GB RAM recommended
- **Storage**: 1GB free space

## Installation Methods

### Method 1: Executable Download (Recommended for End Users)

1. **Download the Latest Release**
   - Visit the [Releases page](https://github.com/yourusername/Medical-Spytool/releases)
   - Download the appropriate executable for your operating system:
     - Windows: `Medical_Spytool.exe`
     - macOS: `Medical_Spytool.app`
     - Linux: `Medical_Spytool`

2. **Run the Application**
   - **Windows**: Double-click `Medical_Spytool.exe`
   - **macOS**: Double-click `Medical_Spytool.app`
   - **Linux**: Make executable and run: `chmod +x Medical_Spytool && ./Medical_Spytool`

### Method 2: Python Installation

#### Prerequisites
```bash
# Ensure Python 3.8+ is installed
python --version

# Update pip
python -m pip install --upgrade pip
```

#### Installation Steps
```bash
# Clone the repository
git clone https://github.com/yourusername/Medical-Spytool.git
cd Medical-Spytool

# Create virtual environment (recommended)
python -m venv medical_spytool_env

# Activate virtual environment
# Windows:
medical_spytool_env\Scripts\activate
# macOS/Linux:
source medical_spytool_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Method 3: Development Installation

```bash
# Clone and setup for development
git clone https://github.com/yourusername/Medical-Spytool.git
cd Medical-Spytool

# Create virtual environment
python -m venv dev_env
source dev_env/bin/activate  # or dev_env\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .

# Run tests to verify installation
pytest
```

## Configuration

### API Keys Setup
Some databases require API keys for enhanced access:

1. **PubMed/NCBI**: 
   - Get your API key from [NCBI](https://www.ncbi.nlm.nih.gov/account/settings/)
   - Add to config file

2. **Configuration File**:
   Create `config.json` in the application directory:
   ```json
   {
     "api_keys": {
       "pubmed": "your_pubmed_api_key",
       "ncbi": "your_ncbi_api_key"
     },
     "default_settings": {
       "max_results": 1000,
       "export_format": "json",
       "timeout": 30
     }
   }
   ```

## Troubleshooting

### Common Issues

#### Issue: "Python not found"
**Solution**: Install Python from [python.org](https://python.org) or use your system package manager.

#### Issue: "Permission denied" on Linux/macOS
**Solution**: 
```bash
chmod +x Medical_Spytool
```

#### Issue: Import errors
**Solution**: 
```bash
pip install -r requirements.txt --force-reinstall
```

#### Issue: GUI not showing on Linux
**Solution**: Install tkinter:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter
```

### Getting Help

- **GitHub Issues**: [Report bugs](https://github.com/yourusername/Medical-Spytool/issues)
- **Discussions**: [Community help](https://github.com/yourusername/Medical-Spytool/discussions)
- **Documentation**: Check the `docs/` directory for more guides
