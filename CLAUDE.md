# Local Crime Statistics Dashboard

## Project Overview
A marimo notebook application that fetches UK crime statistics from the Police.uk API based on postcode and date, stores them in a SQLite database, and visualizes crime locations on an interactive map.

## Current Status
**Completed:** Working implementation with interactive map, chart visualization, and intelligent query caching
**Last Updated:** 2025-11-15 (map visualization and caching added)

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
- **SQLite Database**: `crimes.db` stores all fetched crime data and query cache
- **Duplicate Prevention**: Uses Crime ID as primary key to prevent duplicate entries
- **Intelligent Caching**: Tracks which postcode+month combinations have been fetched to avoid redundant API calls

**Database Schema:**
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

  -- Query cache table (NEW)
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

### 3. Query Caching System (NEW)
- **Automatic Cache Check**: Before calling the API, checks if data for this postcode+month already exists
- **Smart API Usage**: Only calls UK Police API if data not already in database
- **Cache Indicators**: Results clearly show whether data came from:
  - **"✓ (From Cache)"** - Retrieved from database (instant, no API call)
  - **"Fresh from API"** - Just fetched from UK Police API
- **Persistent Cache**: Cached queries survive application restarts
- **Postcode Normalization**: Handles postcodes with/without spaces consistently
- **Empty Result Caching**: Even queries with no crimes are cached to prevent redundant API calls
- **Performance**: Cached queries load instantly vs ~1+ second for API calls

### 4. User Interface
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
  - New records added to database (or "0" if from cache)
  - **Data Source**: Cache with timestamp OR "just fetched" from API
  - **Inline visualizations**: Map and chart display immediately

### 5. Data Visualization
**Two visualization modes displayed together:**

#### A. Interactive Map (Folium)
- **Street-level map tiles**: OpenStreetMap tiles showing actual streets and geography
- **Postcode marker**: Green home icon shows the search location
- **Crime markers**: Colored circle markers for each crime
  - Color-coded by crime category (burglary=red, drugs=purple, etc.)
  - Click to see popup with full details (category, street, month, coordinates)
  - Hover to see crime category
- **Interactive controls**: Pan, zoom, and explore the area
- **Zoom constraints**:
  - Default zoom level 14 (approximately 2.5 mile x 2.5 mile view)
  - Min zoom 13, max zoom 16
  - Implements the 2.5 mile x 2.5 mile constraint from requirements
- **14 crime categories** with distinct colors

#### B. Crime Distribution Chart (Altair)
- **Scatter plot**: Shows crime distribution by lat/lng coordinates
- **Color coding**: Each crime category shown in different color
- **Tooltips**: Hover to see crime details
  - Latitude (formatted to 2 decimal places)
  - Longitude (formatted to 2 decimal places)
  - Street name
- **Interactive**: Built-in Altair interactivity
- **Responsive**: Width set to 'container', height 290px
- **Grid**: Axis grid enabled for better readability

**Display Layout:**
1. Results summary (postcode, coordinates, crime counts)
2. Interactive Map section
3. Crime Distribution Chart section

## Technical Stack

### Libraries Used
- **marimo**: Reactive notebook framework
- **polars**: DataFrame operations and data manipulation
- **altair**: Interactive data visualization (scatter plots)
- **folium**: Interactive map visualization with OpenStreetMap tiles
- **sqlite3**: Local database storage
- **requests**: HTTP API calls
- **datetime/time**: Date handling and rate limiting
- **pathlib**: File path management

### Code Structure (main.py)
1. **Cell 1** (lines 18-29): All imports (including folium)
2. **Cell 2** (lines 32-68): Database initialization function (crimes + query_cache tables)
3. **Cell 3** (lines 71-103): Save crimes to database function
4. **Cell 4** (lines 106-119): Retrieve all crimes from database function (not currently used)
5. **Cell 5** (lines 122-141): **NEW** Check query cache function
6. **Cell 6** (lines 144-158): **NEW** Add to query cache function
7. **Cell 7** (lines 161-175): **NEW** Get filtered crimes from database (by month)
8. **Cell 8** (lines 178-197): Postcode to coordinates conversion
9. **Cell 9** (lines 200-227): Chart creation function using Altair
10. **Cell 10** (lines 230-292): Map creation function using Folium
11. **Cell 11** (lines 295-336): UK Police API fetching with rate limiting
12. **Cell 12** (lines 339-362): UI inputs (postcode, date, run button)
13. **Cell 13** (lines 365-473): Main processing logic with caching, map and chart display

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
1. **No Database View**: Removed separate database visualization cell
   - Can only view crimes from most recent fetch
   - Cannot browse all historical data in database
   - `get_crimes_from_db()` function exists but not currently used

2. **Single Query Display**: Shows only latest query results
   - Cannot compare multiple queries side-by-side
   - No persistent view of accumulated data

3. **No Data Export**: Data stored in SQLite but no export functionality
   - Future: Add CSV/JSON export options

4. **No Category Filtering**: All crimes are displayed
   - Cannot filter map or chart by specific crime categories
   - Shows all 14+ crime types at once

5. **Error Handling**: Basic error handling present but could be more robust
   - API timeout: 10 seconds
   - No retry logic for failed requests

## Future Enhancements

### High Priority
- [ ] Re-add database view cell (optional toggle or separate tab)
  - Would allow browsing all accumulated crime data
  - Consider adding filters by date range, postcode, or category
- [x] ~~Add proper map visualization with tiles (folium or leaflet)~~ **COMPLETED**
  - ✓ Implemented with Folium and OpenStreetMap tiles
  - ✓ 2.5 mile x 2.5 mile zoom constraint implemented
  - ✓ Shows actual streets and geography context
  - ✓ Color-coded crime markers with interactive popups
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
- [x] ~~Cache postcode lookups to reduce API calls~~ **COMPLETED**
  - ✓ Query cache table stores postcode+month combinations
  - ✓ Automatic check before API calls
  - ✓ Instant retrieval from database for cached queries
  - ✓ Clear cache indicators in results
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
- **Folium Docs**: https://python-visualization.github.io/folium/

## Questions for Future Sessions

When picking this up again, consider:

**Visualization:**
1. ✓ Map tiles implemented with Folium (completed 2025-11-15)
2. Should we re-add the database view cell to see all accumulated data?
3. Should we add legend to the map showing crime category colors?

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

### 2025-11-15 (Late Afternoon) - Intelligent Query Caching Implemented

**Session Summary:**
Successfully implemented an intelligent query caching system that eliminates redundant API calls by checking if postcode+month data already exists in the database. The system provides instant results for cached queries and clearly indicates the data source to users.

**Major Features Added:**
- **Query Cache Database Table**: New `query_cache` table tracks fetched postcode+month combinations
  - Stores postcode, month, coordinates, crime count, and fetch timestamp
  - Primary key on (postcode, month) ensures uniqueness
- **Cache Check System**: Automatically checks cache before calling UK Police API
  - Normalizes postcodes (uppercase, no spaces) for consistent matching
  - Returns whether data exists, count, and when it was fetched
- **Smart API Usage**: Only calls API if data not already in database
  - Reduces load on free UK Police API service
  - Significantly speeds up repeat queries (instant vs 1+ second)
- **Empty Result Caching**: Even queries with no crimes are cached
  - Prevents redundant API calls for locations/dates with no crime data
- **Clear User Feedback**: Results display data source
  - "✓ (From Cache)" with timestamp for cached data
  - "Fresh from API (just fetched)" for new API calls
  - Shows whether new API call was made or not
- **Persistent Cache**: Survives application restarts

**Code Changes:**
- Updated `init_database()` to create query_cache table (main.py:32-68)
- Added `check_query_cache()` function (main.py:122-141)
- Added `add_to_query_cache()` function (main.py:144-158)
- Added `get_crimes_from_db_filtered()` function (main.py:161-175)
- Updated main processing logic to check cache first (main.py:365-473)
- Modified result display to show cache status and timestamp

**Completed Requirement:**
- ✓ Medium Priority Enhancement #8: Cache postcode lookups to reduce API calls

**Performance Impact:**
- Cached queries: Instant (<100ms)
- New API queries: ~1+ second (unchanged)
- Significant improvement for repeated postcodes or reviewing historical data

**User Benefits:**
- Faster results for previously queried data
- Reduced API load (respectful of free service)
- Transparent indication of data freshness
- Can query same postcode multiple times for different months efficiently

### 2025-11-15 (Afternoon) - Interactive Map Visualization Added

**Session Summary:**
Successfully implemented proper map visualization with street-level tiles using Folium. The application now displays both an interactive map and the existing chart visualization, giving users geographic context and data distribution views simultaneously.

**Major Features Added:**
- **Folium Integration**: Added folium library (v0.20.0) to dependencies
- **Interactive Street Map**: OpenStreetMap tiles showing actual streets and geography
- **Crime Markers**: Color-coded circle markers for each crime location
  - 14 distinct colors for different crime categories
  - Click markers for detailed popups (category, street, month, coordinates)
  - Hover to see crime category name
- **Postcode Location Marker**: Green home icon shows the search location center
- **Zoom Constraints**: Implemented 2.5 mile x 2.5 mile requirement
  - Default zoom level 14
  - Min zoom 13, max zoom 16
- **Dual Visualization**: Map and chart displayed together in sequence

**Code Changes:**
- Added `create_crime_map()` function (main.py:159-221)
- Updated imports to include folium
- Modified main processing cell to generate and display both map and chart
- Display layout: Results summary → Interactive Map → Crime Distribution Chart

**Completed Requirement:**
- ✓ High Priority Enhancement #2: Proper map visualization with tiles
- ✓ Implements 2.5 mile x 2.5 mile zoom constraint from original requirements
- ✓ Shows actual streets and geographic context

**User Preference Decisions:**
- Chose Folium over Plotly or direct Leaflet integration
- Decided to show both map and chart (not replace chart with map)
- Map appears first, followed by chart

### 2025-11-15 (Morning) - Category Filter Exploration and Reversion

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
