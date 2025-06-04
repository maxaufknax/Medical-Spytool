# Medical-Spytool Configuration Examples

## Command Line Examples

### Basic Searches
```bash
# Single author search
python -m dnb_spytool --author "Johann Wolfgang von Goethe"

# Multiple authors
python -m dnb_spytool --authors "Goethe,Schiller,Heine"

# Specific database
python -m dnb_spytool --author "Einstein" --database pubmed

# Limit results
python -m dnb_spytool --author "Kafka" --max-results 50
```

### Export Options
```bash
# Excel format
python -m dnb_spytool --author "Goethe" --format xlsx --output results.xlsx

# JSON format
python -m dnb_spytool --author "Schiller" --format json --output data.json

# Custom output path
python -m dnb_spytool --author "Heine" --output "/path/to/results.csv"
```

### Analytics
```bash
# Generate analytics report
python -m dnb_spytool --author "Kafka" --analytics

# HTML report
python -m dnb_spytool --author "Mann" --analytics --report-format html

# Combined search with analytics
python -m dnb_spytool --authors "Darwin,Wallace" --analytics --format xlsx
```

### GUI Mode
```bash
# Launch graphical interface
python -m dnb_spytool --gui
```

## Batch File Examples (Windows)

### search_author.bat
```batch
@echo off
echo Searching for author: %1
python -m dnb_spytool --author "%1" --format xlsx --output "%1_results.xlsx"
pause
```

### Usage: `search_author.bat "Johann Wolfgang von Goethe"`

### batch_search.bat
```batch
@echo off
echo Running batch search...
python -m dnb_spytool --authors "Goethe,Schiller,Heine" --analytics --format xlsx
echo Search completed!
pause
```

## Shell Script Examples (Linux/Mac)

### search_author.sh
```bash
#!/bin/bash
echo "Searching for author: $1"
python3 -m dnb_spytool --author "$1" --format xlsx --output "${1// /_}_results.xlsx"
```

### Usage: `./search_author.sh "Johann Wolfgang von Goethe"`

### daily_search.sh
```bash
#!/bin/bash
# Daily automated search
DATE=$(date +%Y%m%d)
python3 -m dnb_spytool --authors "$(cat authors.txt | tr '\n' ',')" \
    --format xlsx --output "daily_search_$DATE.xlsx" --analytics
```

## Integration Examples

### Python Integration
```python
import subprocess
import sys

def search_medical_literature(author, database="dnb", max_results=100):
    """Search medical literature programmatically"""
    cmd = [
        sys.executable, "-m", "dnb_spytool",
        "--author", author,
        "--database", database,
        "--max-results", str(max_results),
        "--format", "json",
        "--output", f"{author.replace(' ', '_')}.json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

### CSV Processing
```python
import pandas as pd

# Load results
df = pd.read_csv("results.csv")

# Basic analysis
print(f"Total publications: {len(df)}")
print(f"Year range: {df['Year'].min()} - {df['Year'].max()}")
print(f"Top publishers: {df['Publisher'].value_counts().head()}")
```
