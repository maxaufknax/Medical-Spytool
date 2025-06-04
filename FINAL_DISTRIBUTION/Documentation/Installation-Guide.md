# Medical-Spytool Installation Guide

## Quick Installation Methods

### Method 1: Portable Application (Easiest)
**No installation required!**

1. Download the distribution package
2. Extract to any folder
3. Navigate to `Portable-App/Medical-Spytool-Portable/`
4. **Windows**: Double-click `Medical-Spytool.bat`
5. **Linux/Mac**: Run `./medical-spytool.sh`

✅ **Advantages**: Works immediately, no dependencies to manage  
❌ **Limitations**: Requires Python to be installed on the system

### Method 2: Windows Executable
**For Windows users who want a standalone .exe file**

1. Copy the `Windows-Executable/` folder to a Windows machine
2. Double-click `build_windows_exe.bat`
3. Wait for the build to complete
4. Find `Medical-Spytool.exe` in the `dist/` folder

✅ **Advantages**: True standalone executable, no Python required  
❌ **Limitations**: Windows only, larger file size

### Method 3: Python Package Installation
**For developers and advanced users**

#### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Internet connection

#### Installation Steps
```bash
# 1. Extract source code
unzip Medical-Spytool-Source.zip
cd Medical-Spytool/

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the package (optional)
pip install -e .

# 4. Run the application
python -m dnb_spytool --help
```

## Platform-Specific Instructions

### Windows

#### Option A: Portable App
1. Extract the ZIP file
2. Go to `Portable-App/Medical-Spytool-Portable/`
3. Double-click `Medical-Spytool.bat`

#### Option B: Build Executable
1. Install Python 3.8+ from https://python.org
2. Extract `Windows-Executable/` files
3. Right-click `build_windows_exe.bat` → "Run as administrator"
4. Wait for completion
5. Run `dist/Medical-Spytool.exe`

#### Option C: Python Installation
```cmd
# Open Command Prompt as Administrator
pip install -r requirements.txt
python -m dnb_spytool --gui
```

### Linux

#### Option A: Portable App
```bash
# Extract and run
unzip Medical-Spytool-Distribution.zip
cd Portable-App/Medical-Spytool-Portable/
chmod +x medical-spytool.sh
./medical-spytool.sh
```

#### Option B: System Installation
```bash
# Install Python and pip (if not installed)
sudo apt update
sudo apt install python3 python3-pip

# Install Medical-Spytool
pip3 install -r requirements.txt
python3 -m dnb_spytool --gui
```

### macOS

#### Option A: Portable App
```bash
# Extract and run
unzip Medical-Spytool-Distribution.zip
cd Portable-App/Medical-Spytool-Portable/
chmod +x medical-spytool.sh
./medical-spytool.sh
```

#### Option B: Homebrew Installation
```bash
# Install Python via Homebrew
brew install python3

# Install Medical-Spytool
pip3 install -r requirements.txt
python3 -m dnb_spytool --gui
```

## Dependency Information

### Required Python Packages
- `requests` - HTTP library for API calls
- `beautifulsoup4` - HTML/XML parsing
- `pandas` - Data manipulation
- `openpyxl` - Excel file support
- `lxml` - XML processing
- `python-dateutil` - Date parsing
- `tqdm` - Progress bars
- `numpy` - Numerical computing

### Optional Packages
- `matplotlib` - Charts and graphs (for analytics)
- `seaborn` - Statistical visualization
- `tkinter` - GUI framework (usually included with Python)

## Verification

### Test Your Installation
```bash
# Check if installation works
python -m dnb_spytool --help

# Test with a simple search
python -m dnb_spytool --author "Goethe" --max-results 5 --validate-only

# Launch GUI
python -m dnb_spytool --gui
```

### Expected Output
- Help message should display all available options
- Validation test should complete without errors
- GUI should open without error messages

## Troubleshooting Installation

### Common Issues

**"Python not found"**
- Install Python from https://python.org
- Make sure Python is added to PATH during installation
- Restart terminal/command prompt after installation

**"pip not found"**
- Python 3.4+ includes pip by default
- Try `python -m pip` instead of `pip`
- Reinstall Python with pip option enabled

**"Permission denied"**
- Use `sudo` on Linux/Mac: `sudo pip install -r requirements.txt`
- Run Command Prompt as Administrator on Windows
- Consider using virtual environments

**"Package conflicts"**
- Use virtual environment: `python -m venv medical_spytool_env`
- Activate environment and install there
- See Python virtual environment documentation

### Virtual Environment Setup (Recommended)
```bash
# Create virtual environment
python -m venv medical_spytool_env

# Activate it
# Windows:
medical_spytool_env\Scripts\activate
# Linux/Mac:
source medical_spytool_env/bin/activate

# Install packages
pip install -r requirements.txt

# Run application
python -m dnb_spytool --gui
```

## Getting Help

- **Documentation**: Check the Documentation folder
- **Examples**: See Examples folder for usage patterns
- **Issues**: Report problems on GitHub
- **Updates**: Check for new versions periodically
