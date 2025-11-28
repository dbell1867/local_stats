# Changelog

All notable changes to the Local Crime Statistics Dashboard project.

## [2025-11-19] - Display Order Optimization

### Changed
- Restructured display flow for uncached postcodes (main.py:677-719, 788-802)
  - Map now displays immediately for requested month
  - Histogram generated AFTER background fetching completes
  - Shows "Fetching historical data in background..." message

### Fixed
- Output size issue diagnosis: Folium maps with many markers are 5-10MB
  - Increased marimo output limit to 20MB in `pyproject.toml`
  - Removed progress print statements to minimize output
  - Removed debug print statement (main.py:636-637)

### Performance
- Map appears immediately (faster perceived performance)
- Complete histogram shows all 30+ months in one view
- No more misleading partial histogram with 1 bar
- 20MB limit provides headroom for high-crime areas

## [2025-11-18] - Critical Bug Fixes and Validation

### Added
- Date validation system via `validate_date_format()` function (main.py:236-282)
  - Validates YYYY-MM format
  - Checks month is 01-12
  - Ensures date is within valid range (2022-10 to latest)
  - Clear error messages for each validation failure

### Fixed
- **CRITICAL:** Location filtering bug in `get_crimes_from_db_filtered()`
  - Previously only filtered by month, returned ALL crimes from database
  - Now filters by both month AND location (0.02 degree radius ≈1.4 miles)
  - Dramatically reduced output size from 29MB+ to normal levels
- Histogram count consistency
  - Updated `get_crime_counts_by_month()` to count actual crimes with location filter
  - Histogram counts now match "Crimes Found" display
- Variable scoping issues
  - Added proper variable tracking with `current_lat`, `current_lng`, `current_postcode`
  - Added `successfully_processed` flag
  - Background fetching only runs if current query succeeded

### Changed
- Simplified histogram visualization (main.py:340-373)
  - Removed interactive selection (changed from `mo.ui.altair_chart()` to regular Altair)
  - Removed `cursor='pointer'` and selection parameters
  - Updated heading to "Crime Trends by Month" (removed "Click a bar to view")
- Disabled histogram selection cell (main.py:738-742)

### Removed
- Interactive month selection via histogram clicking
- Duplicate output from histogram selection cell

### Database
- Cleaned 1 invalid record from query_cache (month "2025-19")

## [2025-11-17] - Histogram, Background Fetching, Data Range Update

### Added
- Interactive crime trends histogram replacing scatter plot
  - Bar chart showing total crimes by month
  - Current month highlighted in red, others in blue
  - Tooltips with exact month and crime count
- `generate_month_range()` function for 2022-10 to present (main.py:251-274)
- `get_crime_counts_by_month()` function for histogram data (main.py:178-200)
- `get_last_updated()` function to check API data availability (main.py:199-223)
- Background historical data fetching
  - Automatically fetches ALL months (2022-10 to present) for queried postcodes
  - Only fetches months not in cache
  - Respects 100ms rate limiting
  - Progress updates every 10 months
- Histogram selection handler cell for interactive month switching (main.py:656-695)

### Changed
- Updated date range from 2015-01 to 2022-10 throughout application
- Replaced scatter plot with histogram visualization
- Main processing cell includes last updated check and background fetching

### Removed
- `chart_crimes()` scatter plot function (replaced by `create_crime_histogram()`)

### Database
- Deleted 93 outdated query_cache entries from before 2022-10

### Performance
- Reduced fetch time from ~120 months to ~27 months for full historical data
- Initial query for new location: ~3-5 seconds (27 months with rate limiting)
- Subsequent month changes: Instant (cached data)
- Histogram rendering: <100ms
- Map updates on bar click: <500ms

## [2025-11-15 - Late Afternoon] - Query Caching System

### Added
- `query_cache` database table (main.py:32-68)
  - Tracks postcode+month combinations already fetched
  - Stores postcode, month, coordinates, crime count, timestamp
  - Primary key on (postcode, month)
- `check_query_cache()` function (main.py:122-141)
  - Normalizes postcodes (uppercase, no spaces)
  - Returns cache status, count, and fetch timestamp
- `add_to_query_cache()` function (main.py:144-158)
- `get_crimes_from_db_filtered()` function (main.py:161-175)
- Clear user feedback for data source
  - "✓ (From Cache)" with timestamp for cached data
  - "Fresh from API (just fetched)" for new API calls

### Changed
- Main processing logic checks cache before calling API
- Empty results are now cached to prevent redundant API calls

### Performance
- Cached queries: <100ms (instant)
- New API queries: ~1+ second (unchanged)
- Significant improvement for repeated postcodes

## [2025-11-15 - Afternoon] - Interactive Map Visualization

### Added
- Folium integration (v0.20.0)
- `create_crime_map()` function (main.py:159-221)
  - OpenStreetMap tiles with street-level detail
  - Color-coded circle markers for crimes (14 categories)
  - Click markers for detailed popups
  - Hover to see crime category
- Green home icon marker for postcode location
- Zoom constraints (default 14, min 13, max 16)
  - Implements 2.5 mile x 2.5 mile requirement

### Changed
- Display layout: Results → Interactive Map → Chart
- Both map and chart displayed together

## [2025-11-15 - Morning] - Category Filter Exploration (Reverted)

### Attempted
- Crime category dropdown filter with 15 UK crime types
- Post-fetch filtering by selected category

### Reverted
- KeyError when displaying category names
- Returned to stable version
- Category filtering moved to future enhancements

### Lessons Learned
- Keep features simple, test thoroughly
- Current stable version meets core requirements

## [2025-11-14 - Evening] - UI Fixes and Inline Chart

### Added
- `chart_crimes()` function for inline Altair charts (lines 118-145)
  - Scatter plot with lat/lng points
  - Tooltips showing coordinates (2 decimal places) and month
  - Responsive width, 290px height

### Changed
- Switched from `mo.ui.button` to `mo.ui.run_button` (line 209)
  - Fixed button reactivity issue
- API endpoint from `crimes-at-location` to `crimes-street/all-crime` (line 157)
  - New endpoint returns 1 mile radius (area-based)
  - Provides better neighborhood-level crime context
- Chart displays inline with results using `mo.vstack()`
- Uses `mo.output.replace()` for proper display

### Removed
- Separate database visualization cell
- `db_path` export (database view removed)

## [2025-11-14 - Initial] - Initial Implementation

### Added
- Marimo notebook structure
- UK Police API integration
- Postcode to coordinates conversion (postcodes.io)
- SQLite database with crimes table
- UI with postcode input, date input, button
- Altair visualization
- Rate limiting (100ms delay, 10 req/sec)
- Duplicate checking by Crime ID
- Default date to last month
