# User Manual

## Getting Started

Medical Spytool provides both graphical (GUI) and command-line (CLI) interfaces for searching medical literature.

## GUI Interface

### Launching the GUI
```bash
python src/main.py
```
or double-click the executable file.

### Main Interface Components

1. **Search Tab**
   - **Search Terms**: Enter keywords, phrases, or advanced queries
   - **Database Selection**: Choose from PubMed, DNB, or multiple databases
   - **Filters**: Set date ranges, author filters, journal restrictions
   - **Max Results**: Limit the number of results (default: 100)

2. **Results Tab**
   - **Results Table**: Display search results with title, authors, journal, date
   - **Preview Panel**: Show abstract and details for selected articles
   - **Export Options**: Save results in various formats

3. **Settings Tab**
   - **API Configuration**: Set up database API keys
   - **Default Preferences**: Configure default search parameters
   - **Export Settings**: Choose default export formats and locations

### Search Examples

#### Basic Search
1. Enter search terms: `diabetes treatment`
2. Select database: `PubMed`
3. Click "Search"

#### Advanced Search
1. Enter: `"machine learning" AND medicine`
2. Set date range: 2020-2023
3. Add author filter: `Smith`
4. Select multiple databases
5. Click "Search"

#### Batch Search
1. Go to "Batch" tab
2. Upload text file with search terms (one per line)
3. Configure search parameters
4. Click "Start Batch Search"

## CLI Interface

### Basic Commands

#### Simple Search
```bash
python src/main.py --search "diabetes treatment" --database pubmed
```

#### Advanced Search with Filters
```bash
python src/main.py \
  --search "covid-19 vaccines" \
  --database pubmed,dnb \
  --year-from 2020 \
  --year-to 2023 \
  --max-results 500 \
  --export results.json
```

#### Batch Processing
```bash
python src/main.py \
  --batch queries.txt \
  --output-dir ./results/ \
  --format json
```

### CLI Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--search` | Search terms | `"diabetes treatment"` |
| `--database` | Database(s) to search | `pubmed`, `dnb`, `pubmed,dnb` |
| `--year-from` | Start year filter | `2020` |
| `--year-to` | End year filter | `2023` |
| `--author` | Author filter | `"Smith J"` |
| `--journal` | Journal filter | `"Nature"` |
| `--max-results` | Maximum results | `100` |
| `--export` | Export file path | `results.json` |
| `--format` | Export format | `json`, `csv`, `excel` |
| `--batch` | Batch file path | `queries.txt` |
| `--output-dir` | Output directory | `./results/` |

## Search Syntax

### Basic Queries
- Single terms: `diabetes`
- Multiple terms: `diabetes treatment`
- Phrases: `"type 2 diabetes"`

### Boolean Operators
- AND: `diabetes AND treatment`
- OR: `diabetes OR "blood sugar"`
- NOT: `diabetes NOT "type 1"`

### Field-Specific Searches
- Author: `author:"Smith J"`
- Title: `title:"diabetes treatment"`
- Journal: `journal:"Nature Medicine"`
- Year: `year:2020-2023`

### Advanced Syntax
- Wildcards: `diabet*` (matches diabetes, diabetic, etc.)
- Proximity: `diabetes NEAR/5 treatment`
- Exact phrase: `"machine learning in medicine"`

## Export Formats

### Supported Formats
- **JSON**: Machine-readable format
- **CSV**: Spreadsheet compatible
- **Excel**: Full Excel workbook with multiple sheets
- **XML**: Structured markup
- **BibTeX**: Reference manager compatible
- **RIS**: Citation format

### Export Options
- **Full Results**: All search results
- **Selected Results**: Only checked items
- **Summary Only**: Titles and basic info
- **Detailed**: Include abstracts and full metadata

## Database Information

### PubMed
- **Coverage**: 30+ million citations
- **Focus**: Biomedical and life sciences
- **Update Frequency**: Daily
- **API Limits**: 3 requests/second (with API key: 10/second)

### DNB (Deutsche Nationalbibliothek)
- **Coverage**: German publications
- **Focus**: All subjects including medicine
- **Update Frequency**: Weekly
- **Access**: Open access, no API key required

## Tips and Best Practices

### Search Optimization
1. **Start Broad**: Begin with general terms, then refine
2. **Use Synonyms**: Include alternative terms
3. **Check Spelling**: Verify scientific terms
4. **Use Filters**: Narrow results with date/author filters

### Performance Tips
1. **Batch Searches**: Use batch mode for multiple queries
2. **Reasonable Limits**: Don't request too many results at once
3. **API Keys**: Use API keys for better performance
4. **Save Progress**: Export intermediate results

### Troubleshooting
1. **No Results**: Try broader terms or different spellings
2. **Too Many Results**: Add more specific filters
3. **Slow Searches**: Check internet connection, reduce result limits
4. **Export Issues**: Ensure write permissions for output directory

## Keyboard Shortcuts

### GUI Shortcuts
- `Ctrl+N`: New search
- `Ctrl+S`: Save/Export results
- `Ctrl+F`: Focus search box
- `Ctrl+Q`: Quit application
- `F1`: Show help
- `F5`: Refresh results

## API Integration

### Python API Example
```python
from dnb_spytool import MedicalSpytool

# Initialize
spytool = MedicalSpytool()

# Configure
spytool.set_api_key('pubmed', 'your_api_key')

# Search
results = spytool.search_pubmed('diabetes treatment', max_results=100)

# Filter results
recent_results = spytool.filter_by_year(results, 2020, 2023)

# Export
spytool.export_json(recent_results, 'diabetes_recent.json')
```

### REST API
If running as a service:
```bash
# Start API server
python src/api_server.py

# Make requests
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes", "database": "pubmed", "max_results": 10}'
```
