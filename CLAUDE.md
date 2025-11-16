# Local Crime Statistics Dashboard

## Project Overview
A marimo notebook application that fetches UK crime statistics from the Police.uk API based on postcode and date, stores them in a SQLite database, and visualizes crime locations on an interactive map.

## Current Status
**Completed:** Working implementation with inline chart visualization
**Last Updated:** 2025-11-15

## Features Implemented

### 1. Data Collection
- **Postcode to Coordinates Conversion**: Uses postcodes.io API to convert UK postcodes to latitude/longitude
- **UK Police API Integration**: Fetches crime data in area around postcode
  - Uses `crimes-street/all-crime` endpoint
  - Returns crimes within **1 mile radius** of coordinates
  - Provides neighborhood-level crime context
- **Rate Limiting**: Implements 100ms delay between API calls (max 10 requests/second)
- **Data Extraction**: Captures:
  - Crime Category
  - Crime ID
  - Location latitude
  - Location longitude
  - Street name
  - Month (date of crime)

### 2. Data Storage
- **SQLite Database**: `crimes.db` stores all fetched crime data
- **Duplicate Prevention**: Uses Crime ID as primary key to prevent duplicate entries
- **Schema**:
  ```sql
  CREATE TABLE crimes (
      id TEXT PRIMARY KEY,
      category TEXT,
      month TEXT,
      lat REAL,
      lng REAL,
      street_name TEXT
  )
  ```

### 3. User Interface
- **Postcode Input**: Text field for entering UK postcodes (e.g., "SW1A 1AA")
- **Date Input**: Text field for year-month format (e.g., "2024-01")
  - Default: Previous month from today
- **Run Button**: `mo.ui.run_button` triggers data fetch and processing
  - Changed from `mo.ui.button` to fix reactivity issues
- **Results Display**: Shows:
  - Postcode entered
  - Coordinates found
  - Date queried
  - Total crimes found
  - New records added to database
  - **Inline Chart**: Displays immediately after fetch

### 4. Data Visualization
- **Inline Chart**: Altair scatter plot shown immediately after data fetch
- **Color Coding**: Each crime category shown in different color
- **Tooltips**: Hover to see crime details
  - Latitude (formatted to 2 decimal places)
  - Longitude (formatted to 2 decimal places)
  - Month
- **Interactive**: Built-in Altair interactivity
- **Responsive**: Width set to 'container', height 290px
- **Grid**: Axis grid enabled for better readability
- **NOTE**: Separate database visualization cell removed for simplicity

## Technical Stack

### Libraries Used
- **marimo**: Reactive notebook framework
- **polars**: DataFrame operations and data manipulation
- **altair**: Interactive data visualization
- **sqlite3**: Local database storage
- **requests**: HTTP API calls
- **datetime/time**: Date handling and rate limiting
- **pathlib**: File path management

### Code Structure (main.py)
1. **Cell 1** (lines 8-18): All imports
2. **Cell 2** (lines 22-43): Database initialization function
3. **Cell 3** (lines 47-78): Save crimes to database function
4. **Cell 4** (lines 82-94): Retrieve crimes from database function (not currently used)
5. **Cell 5** (lines 98-115): Postcode to coordinates conversion
6. **Cell 6** (lines 119-145): Chart creation function using Altair
7. **Cell 7** (lines 149-189): UK Police API fetching with rate limiting
8. **Cell 8** (lines 193-216): UI inputs (postcode, date, run button)
9. **Cell 9** (lines 220-282): Main processing logic with inline chart display

## API Endpoints Used

### UK Police API
- **Endpoint**: `https://data.police.uk/api/crimes-street/all-crime` (CURRENT)
  - Returns crimes within **1 mile radius** of the specified point
  - Provides area-level crime data around a location
  - **Preferred** for broader crime context in a neighborhood

- **Previous Endpoint**: `https://data.police.uk/api/crimes-at-location` (commented out, line 156)
  - Returns crimes at a **precise location** only
  - More limited data - only crimes at exact coordinates
  - Switched because area-based queries are more useful

- **Parameters**:
  - `date`: YYYY-MM format
  - `lat`: Latitude (decimal)
  - `lng`: Longitude (decimal)
- **Rate Limit**: 15 requests per second (we use 10/sec to be safe)
- **Authentication**: None required
- **Documentation**: https://data.police.uk/docs/

### Postcodes.io API
- **Endpoint**: `https://api.postcodes.io/postcodes/{postcode}`
- **Authentication**: None required
- **Free**: No API key needed
- **Returns**: Latitude and longitude for valid UK postcodes

## How to Run

### Installation
```bash
# Install dependencies (if using uv)
uv sync

# Or with pip
pip install marimo polars altair requests
```

### Running the Notebook
```bash
# Edit mode (interactive development)
marimo edit main.py

# Run mode (view only)
marimo run main.py
```

### Using the Application
1. Enter a UK postcode (e.g., "SW1A 1AA", "M1 1AE")
2. Optionally modify the date (defaults to last month)
3. Click "Fetch Crimes" button
4. View results and map visualization
5. Repeat with different postcodes/dates to build up database

## Files in Project

- `main.py`: Main marimo notebook application
- `crimes.db`: SQLite database (created on first run)
- `reqs.txt`: Requirements and specifications
- `CLAUDE.md`: This documentation file
- `README.md`: General project readme
- `pyproject.toml`: Python project configuration
- `uv.lock`: Dependency lock file

## Known Limitations

### Current Implementation
1. **Map Visualization**: Uses Altair scatter plot, not actual map tiles
   - Shows lat/lng coordinates as X/Y axis
   - For proper map tiles, would need folium or similar library
   - No zoom constraint implemented (requirement: 2.5 mile x 2.5 mile)
   - Note: API returns crimes within 1 mile radius, so displayed area is ~2 miles diameter

2. **No Database View**: Removed separate database visualization cell
   - Can only view crimes from most recent fetch
   - Cannot browse all historical data in database
   - `get_crimes_from_db()` function exists but not currently used

3. **Single Query Display**: Shows only latest query results
   - Cannot compare multiple queries side-by-side
   - No persistent view of accumulated data

4. **No Data Export**: Data stored in SQLite but no export functionality
   - Future: Add CSV/JSON export options

5. **Error Handling**: Basic error handling present but could be more robust
   - API timeout: 10 seconds
   - No retry logic for failed requests

## Future Enhancements

### High Priority
- [ ] Re-add database view cell (optional toggle or separate tab)
  - Would allow browsing all accumulated crime data
  - Consider adding filters by date range, postcode, or category
- [ ] Add proper map visualization with tiles (folium or leaflet)
  - Implement 2.5 mile x 2.5 mile zoom constraint per requirements
  - Show actual streets and geography context
- [ ] Add data export functionality (CSV, JSON)
  - Export current query results
  - Export entire database
- [ ] Add ability to clear/manage database entries
  - Delete by date range
  - Delete by postcode/area
  - Clear entire database

### Medium Priority
- [ ] Add date range queries (multiple months at once)
  - Batch query with rate limiting
  - Progress indicator for long queries
- [ ] Add crime statistics summary (counts by category)
  - Bar chart of crime types
  - Comparison across different postcodes
- [ ] Add comparison view (different time periods)
  - Side-by-side charts
  - Trend over time
- [ ] Cache postcode lookups to reduce API calls
  - Store in database or separate cache file
- [ ] Add category filtering to visualizations
  - Dropdown or checkboxes to filter displayed crime types
  - Show all categories or filter to specific ones

### Low Priority
- [ ] Add multiple postcode batch processing
  - Query multiple postcodes in one session
- [ ] Add historical trend analysis
  - Line charts over time
  - Seasonal patterns
- [ ] Add heat map visualization option
  - Density-based visualization
- [ ] Add crime category descriptions/explanations
  - Help text explaining UK crime categories
- [ ] Add export of map visualizations
  - Save charts as PNG/SVG

## Troubleshooting

### Common Issues

**Button not working / Results not updating**
- Make sure you're using `mo.ui.run_button` not `mo.ui.button`
- `run_button` is designed for operations that trigger computations
- Check that the button cell properly exports `submit_button`

**"Invalid postcode"**
- Check postcode format is correct (UK postcodes only)
- Ensure internet connection for postcodes.io API
- Try with and without spaces (e.g., "SW1A1AA" or "SW1A 1AA")

**"No crimes found"**
- Try different dates (API has historical data limits)
- Some locations may have no reported crimes
- Check date format is YYYY-MM
- Try a different postcode to verify API is working

**"API Error: Status XXX"**
- 503: Police API temporarily unavailable
- 429: Rate limit exceeded (unlikely with our 100ms delay)
- Check internet connection
- Try again after a few minutes

**Chart not displaying**
- Ensure `crimes_fetched` is converted to Polars DataFrame before charting
- Check that chart is wrapped in `mo.ui.altair_chart()`
- Verify chart is included in `mo.vstack()` or displayed via `mo.output.replace()`

**Database errors**
- Delete `crimes.db` and restart to reset database
- Check write permissions in directory
- Ensure SQLite3 is properly installed

## Development Notes

### Design Decisions
1. **Polars over Pandas**: Faster, more memory efficient, better type handling
2. **Altair over Matplotlib**: Interactive, declarative, better for web notebooks
3. **SQLite over CSV**: Structured queries, duplicate checking, better for growing data
4. **postcodes.io**: Free, no API key, reliable for UK postcodes
5. **Rate limiting**: Conservative 10 req/sec to be respectful of free API

### Code Conventions
- One function per cell (marimo requirement)
- All imports in first cell
- Descriptive docstrings for each function
- Error handling with try/except
- Clear variable names

## Resources

- **Marimo Docs**: https://docs.marimo.io/
- **UK Police API**: https://data.police.uk/docs/
- **Postcodes.io**: https://postcodes.io/
- **Polars Docs**: https://pola-rs.github.io/polars/
- **Altair Docs**: https://altair-viz.github.io/

## Questions for Future Sessions

When picking this up again, consider:

**Visualization:**
1. Do we want proper map tiles (folium/leaflet) or is the current scatter plot sufficient?
2. Should we re-add the database view cell to see all accumulated data?
3. How should we implement the 2.5 mile x 2.5 mile zoom constraint from requirements?

**Data Management:**
4. Do we need data export functionality (CSV/JSON)? For what use cases?
5. Should we add ability to delete/manage database entries?
6. How long should we keep historical data?

**API & Data Collection:**
7. Should we add support for querying multiple months at once?
8. Do we need to cache postcode lookups?
9. Should we add support for custom radius queries (currently fixed at 1 mile)?

**Features:**
10. Do we want crime trend analysis over time?
11. Should we add crime category statistics/summaries?
12. Do we need comparison views (different postcodes or time periods)?
13. Should we add category filtering to the visualization?

**User Experience:**
14. ✓ Inline chart display is working well (confirmed 2025-11-14)
15. Do we need progress indicators for long-running queries?
16. Should there be help text explaining UK crime categories?

## Change Log

### 2025-11-15 - Category Filter Exploration and Reversion

**Session Summary:**
Explored adding a category dropdown filter to allow users to filter displayed crimes by type. After implementation, encountered KeyError issues and the user decided to revert to the previous stable version. The stable version includes improved tooltip formatting showing lat/lng with 2 decimal precision.

**What was attempted:**
- Added a crime category dropdown with 15 UK crime types (all-crime, burglary, drugs, violent-crime, etc.)
- Modified main processing logic to filter displayed crimes by selected category
- API calls remained unchanged (still fetching all crime types)
- Chart would filter data post-fetch based on dropdown selection

**Why it was reverted:**
- KeyError when attempting to display category names in results
- User preferred to return to stable, working version
- Category filtering moved to "Medium Priority" future enhancements list

**Current stable state (after reversion):**
- UI has postcode input, date input, and submit button only
- Tooltips display latitude and longitude (formatted to 2 decimal places) plus month
- All crimes fetched are displayed without filtering
- Inline chart visualization working correctly

**Lessons learned:**
- Keep features simple and test thoroughly before adding complexity
- Category filtering is a desired feature but needs more robust implementation
- Current stable version meets core requirements effectively

### 2025-11-14 (Evening) - UI Fixes and Chart Implementation

**Session Summary:**
Successfully debugged and fixed button reactivity issues. Implemented inline chart visualization that displays immediately after fetching crime data. Switched to better API endpoint that provides 1-mile radius coverage. Application now fully functional with working UI, data fetching, database storage, and visualization. User satisfied with current progress.

**Decisions Made:**
- ✓ Inline chart display works well (will revisit if needed)
- ✓ Database view functionality removed for simplicity (may revisit later)
- ✓ `crimes-street/all-crime` endpoint preferred (1 mile radius vs precise location)

**Fixed button reactivity issue:**
- Changed `mo.ui.button` to `mo.ui.run_button` (line 209) - fixed issue where button wasn't triggering properly

**Added inline chart visualization:**
- Created `chart_crimes()` function (lines 118-145) to generate Altair charts
- Chart displays immediately after fetching crimes, not in separate cell
- Uses `mark_point()` for scatter plot style
- Tooltips show lat/lng (2 decimal places) and month
- Width set to 'container' for responsiveness, height 290px
- Axis grid enabled for better readability

**API endpoint change:**
- Switched from `crimes-at-location` to `crimes-street/all-crime` (line 157)
- Old endpoint commented out but preserved in code
- **Key difference**: New endpoint returns crimes within 1 mile radius (area-based)
- **Reason**: Provides more useful neighborhood-level crime data vs. single precise location
- Preferred for getting broader context of crime in an area

**Code cleanup:**
- Removed separate database visualization cell (was at bottom)
- Simplified return statements in cells (lines 94, 282)
- `db_path` no longer exported since database view removed
- Used `mo.vstack()` to display results text and chart together

**Display improvements:**
- Chart appears inline with results summary
- Uses `mo.output.replace()` to properly display results
- Results include both markdown summary and interactive chart

### 2025-11-14 (Initial) - Initial Implementation
- Created marimo notebook structure
- Implemented UK Police API integration
- Added postcode to coordinates conversion
- Created SQLite database with schema
- Built UI with inputs and button
- Added Altair visualization
- Implemented rate limiting
- Added duplicate checking by Crime ID
- Default date to last month
