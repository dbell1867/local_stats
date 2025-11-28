# Local Crime Statistics Dashboard

## Project Overview
A marimo notebook application that fetches UK crime statistics from the Police.uk API based on postcode and date, stores them in a SQLite database, and visualizes crime locations on an interactive map.

## Key Features
- **Postcode-based crime search** with automatic coordinate conversion
- **Intelligent query caching** for instant repeat queries
- **Interactive Folium map** with color-coded crime markers
- **Crime trends histogram** showing historical patterns
- **Background data fetching** for comprehensive historical records
- **Location-based filtering** (~1.4 mile radius)
- **Date validation** (2022-10 to present)

## Technical Stack

### Required Libraries
- `marimo` (v0.17.8+) - Reactive notebook framework
- `polars` - DataFrame operations
- `altair` - Data visualization
- `folium` - Interactive maps
- `sqlite3` - Database storage
- `requests` - API calls

### Configuration
**Marimo Output Limit:** Set to 20MB in `pyproject.toml` to accommodate large Folium maps:
```toml
[tool.marimo.runtime]
output_max_bytes = 20_000_000
```
**Note:** Requires marimo restart after changes.

## Database Schema

```sql
-- Crime data table
CREATE TABLE crimes (
    id TEXT PRIMARY KEY,
    category TEXT,
    month TEXT,
    lat REAL,
    lng REAL,
    street_name TEXT
)

-- Query cache table
CREATE TABLE query_cache (
    postcode TEXT,
    month TEXT,
    lat REAL,
    lng REAL,
    crimes_count INTEGER,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (postcode, month)
)
```

## API Endpoints

### UK Police API
- **Crime Data:** `https://data.police.uk/api/crimes-street/all-crime`
  - Returns crimes within 1 mile radius
  - Data available: October 2022 onwards (2022-10 to present)
  - Parameters: `date` (YYYY-MM), `lat`, `lng`
- **Last Updated:** `https://data.police.uk/api/crime-last-updated`
  - Returns most recent data availability date
- **Rate Limit:** 15 req/sec (we use 10/sec with 100ms delay)
- **Documentation:** https://data.police.uk/docs/

### Postcodes.io API
- **Endpoint:** `https://api.postcodes.io/postcodes/{postcode}`
- **Free, no authentication required**
- Returns latitude/longitude for UK postcodes

## Installation & Usage

```bash
# Install dependencies
uv sync
# OR
pip install marimo polars altair folium requests

# Run the notebook
marimo edit main.py   # Edit mode
marimo run main.py    # Run mode
```

### Using the Application
1. Enter UK postcode (e.g., "SW1A 1AA")
2. Optionally modify date (defaults to last month, format: YYYY-MM)
3. Click "Fetch Crimes" button
4. View interactive map and crime trends histogram

## Performance Notes

### Query Caching
- **Cached queries:** <100ms (instant)
- **New queries:** ~1+ second API call + background fetching
- **Background fetching:** Automatically fetches all historical data (2022-10 to present) for new postcodes

### Location Filtering
- All queries filter to **~1.4 mile radius** (0.02 degrees) around the postcode
- Ensures displayed crimes match the queried location
- Histogram counts match map display

### Display Flow
**Cached postcodes:**
1. Results summary → Crime trends histogram → Interactive map

**Uncached postcodes:**
1. Results summary → Interactive map (immediate)
2. Background fetching runs (all months)
3. Crime trends histogram (appears after fetching)

## Troubleshooting

### Common Issues

**Button not working**
- Ensure using `mo.ui.run_button` not `mo.ui.button`

**Invalid date errors**
- Format must be YYYY-MM (e.g., "2024-01" not "2024-1")
- Month must be 01-12
- Date must be between 2022-10 and latest available data

**Output too large error**
- Check `pyproject.toml` has `output_max_bytes = 20_000_000`
- Restart marimo after changes
- Can increase to 30MB if needed

**API errors**
- 503: Police API temporarily unavailable
- 429: Rate limit exceeded (rare with 100ms delay)
- Check internet connection

**Database errors**
- Delete `crimes.db` to reset
- Check write permissions

## Known Limitations

1. **No database view** - Can only see crimes from current query
2. **Single query display** - Cannot compare multiple queries side-by-side
3. **No data export** - No CSV/JSON export functionality
4. **No category filtering** - All crime types displayed together
5. **No interactive month selection** - Must submit new query for different months
6. **Basic error handling** - No retry logic for failed requests

## Design Decisions

1. **Polars over Pandas** - Faster, more memory efficient
2. **Altair over Matplotlib** - Interactive, declarative
3. **SQLite over CSV** - Structured queries, duplicate checking
4. **Location filtering at ~1.4 miles** - Matches Police API 1-mile radius behavior
5. **Background fetching** - Builds comprehensive historical database on first query
6. **20MB output limit** - Accommodates large maps with 200+ crime markers

## Code Conventions
- One function per cell (marimo requirement)
- All imports in first cell
- Descriptive docstrings
- Error handling with try/except
- Clear variable names

## Resources
- **Marimo:** https://docs.marimo.io/
- **UK Police API:** https://data.police.uk/docs/
- **Postcodes.io:** https://postcodes.io/
- **Polars:** https://pola-rs.github.io/polars/
- **Altair:** https://altair-viz.github.io/
- **Folium:** https://python-visualization.github.io/folium/
