# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "polars==1.35.2",
#     "requests==2.32.5",
#     "folium==0.20.0",
# ]
# ///

import marimo

__generated_with = "0.17.8"
app = marimo.App(width="medium")


@app.cell
def _():
    #All imports in first cell
    import marimo as mo
    import polars as pl
    import altair as alt
    import sqlite3
    import requests
    import time
    import folium
    from datetime import datetime, timedelta
    from pathlib import Path
    return (
        Path,
        alt,
        datetime,
        folium,
        mo,
        pl,
        requests,
        sqlite3,
        time,
        timedelta,
    )


@app.cell
def _(Path, sqlite3):
    def init_database():
        """Initialize SQLite database with crimes table and query cache"""
        db_path = Path("crimes.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create crimes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crimes (
                id TEXT PRIMARY KEY,
                category TEXT,
                month TEXT,
                lat REAL,
                lng REAL,
                street_name TEXT
            )
        """)

        # Create query cache table to track what's been fetched
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                postcode TEXT,
                month TEXT,
                lat REAL,
                lng REAL,
                crimes_count INTEGER,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (postcode, month)
            )
        """)

        conn.commit()
        conn.close()
        return str(db_path)
    return (init_database,)


@app.cell
def _(sqlite3):
    def save_crimes_to_db(crimes_data, db_path):
        """Save crime data to database, checking for duplicates by ID"""
        if not crimes_data:
            return 0

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        new_records = 0
        for crime in crimes_data:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO crimes (id, category, month, lat, lng, street_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    crime['id'],
                    crime['category'],
                    crime['month'],
                    crime['lat'],
                    crime['lng'],
                    crime['street_name']
                ))
                if cursor.rowcount > 0:
                    new_records += 1
            except Exception as e:
                print(f"Error inserting crime {crime.get('id')}: {e}")

        conn.commit()
        conn.close()
        return new_records
    return (save_crimes_to_db,)


@app.cell
def _(pl, sqlite3):
    def get_crimes_from_db(db_path):
        """Retrieve all crimes from database as Polars DataFrame"""
        conn = sqlite3.connect(db_path)

        df = pl.read_database(
            "SELECT * FROM crimes",
            connection=conn
        )

        conn.close()
        return df
    return


@app.cell
def _(sqlite3):
    def check_query_cache(db_path, postcode, month):
        """Check if we've already fetched data for this postcode+month combination"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT crimes_count, fetched_at
            FROM query_cache
            WHERE postcode = ? AND month = ?
        """, (postcode.upper().replace(' ', ''), month))

        result = cursor.fetchone()
        conn.close()

        if result:
            return True, result[0], result[1]  # (exists, count, timestamp)
        return False, 0, None
    return (check_query_cache,)


@app.cell
def _(sqlite3):
    def add_to_query_cache(db_path, postcode, month, lat, lng, crimes_count):
        """Add a query to the cache after fetching from API"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO query_cache (postcode, month, lat, lng, crimes_count)
            VALUES (?, ?, ?, ?, ?)
        """, (postcode.upper().replace(' ', ''), month, lat, lng, crimes_count))

        conn.commit()
        conn.close()
    return (add_to_query_cache,)


@app.cell
def _(pl, sqlite3):
    def get_crimes_from_db_filtered(db_path, month, center_lat, center_lng, radius_degrees=0.02):
        """Retrieve crimes from database for a specific month and location

        Args:
            db_path: Path to database
            month: Month in YYYY-MM format
            center_lat: Center latitude of search
            center_lng: Center longitude of search
            radius_degrees: Search radius in degrees (default 0.02 ≈ 1.4 miles)
        """
        conn = sqlite3.connect(db_path)

        # Filter by month and location (bounding box)
        # The Police API returns crimes within ~1 mile, so we use similar filtering
        df = pl.read_database(
            """
            SELECT * FROM crimes
            WHERE month = ?
            AND lat BETWEEN ? AND ?
            AND lng BETWEEN ? AND ?
            """,
            connection=conn,
            execute_options={"parameters": (
                month,
                center_lat - radius_degrees,
                center_lat + radius_degrees,
                center_lng - radius_degrees,
                center_lng + radius_degrees
            )}
        )

        conn.close()
        return df
    return (get_crimes_from_db_filtered,)


@app.cell
def _(pl, sqlite3):
    def get_crime_counts_by_month(db_path, postcode, center_lat, center_lng, radius_degrees=0.02):
        """Get crime counts grouped by month for a specific location

        Counts actual crimes in the database filtered by location, not cached counts.
        This ensures histogram counts match the displayed crime counts.

        Args:
            db_path: Path to database
            postcode: Postcode being queried
            center_lat: Center latitude of search
            center_lng: Center longitude of search
            radius_degrees: Search radius in degrees (default 0.02 ≈ 1.4 miles)
        """
        conn = sqlite3.connect(db_path)

        # First, get all months that have been cached for this postcode
        cached_months_query = """
            SELECT DISTINCT month
            FROM query_cache
            WHERE postcode = ?
            ORDER BY month
        """

        cursor = conn.cursor()
        cursor.execute(cached_months_query, (postcode.upper().replace(' ', ''),))
        cached_months = [row[0] for row in cursor.fetchall()]

        # Now count actual crimes for each month, filtered by location
        if cached_months:
            # Build query to count crimes by month within the location radius
            month_placeholders = ','.join(['?'] * len(cached_months))
            count_query = f"""
                SELECT month, COUNT(*) as crimes_count
                FROM crimes
                WHERE month IN ({month_placeholders})
                AND lat BETWEEN ? AND ?
                AND lng BETWEEN ? AND ?
                GROUP BY month
                ORDER BY month
            """

            df = pl.read_database(
                count_query,
                connection=conn,
                execute_options={"parameters": (
                    *cached_months,
                    center_lat - radius_degrees,
                    center_lat + radius_degrees,
                    center_lng - radius_degrees,
                    center_lng + radius_degrees
                )}
            )
        else:
            # No cached months, return empty dataframe
            df = pl.DataFrame({"month": [], "crimes_count": []})

        conn.close()
        return df
    return (get_crime_counts_by_month,)


@app.cell
def _(requests):
    def postcode_to_coordinates(postcode):
        """Convert UK postcode to latitude and longitude"""
        try:
            # Using postcodes.io API (free, no key required)
            url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data['status'] == 200:
                    return data['result']['latitude'], data['result']['longitude']

            return None, None
        except Exception as e:
            print(f"Error converting postcode: {e}")
            return None, None
    return (postcode_to_coordinates,)


@app.cell
def _(datetime):
    def validate_date_format(date_str, last_updated=None):
        """Validate that date string is in YYYY-MM format with valid month and within data range

        Args:
            date_str: Date string to validate
            last_updated: Most recent date available from API (optional)

        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not date_str or not isinstance(date_str, str):
            return False, "Date is required"

        # Check basic format
        if len(date_str) != 7 or date_str[4] != '-':
            return False, "Date must be in YYYY-MM format (e.g., 2024-01)"

        try:
            # Try to parse the date
            date_obj = datetime.strptime(date_str, "%Y-%m")

            # UK Police API data starts from 2022-10
            min_date = datetime.strptime("2022-10", "%Y-%m")
            if date_obj < min_date:
                return False, f"Date must be 2022-10 or later (UK Police API data starts from October 2022)"

            # Check against last_updated if provided
            if last_updated:
                max_date = datetime.strptime(last_updated, "%Y-%m")
                if date_obj > max_date:
                    return False, f"Date cannot be after {last_updated} (most recent data available)"

            return True, None

        except ValueError as e:
            # Extract month value if possible to give better error message
            try:
                parts = date_str.split('-')
                if len(parts) == 2:
                    month = int(parts[1])
                    if month < 1 or month > 12:
                        return False, f"Invalid month '{parts[1]}'. Month must be between 01 and 12"
            except:
                pass
            return False, f"Invalid date format: {str(e)}"
    return (validate_date_format,)


@app.cell
def _(datetime, requests):
    def get_last_updated():
        """Get the date of the most recent crime data available from Police API"""
        try:
            url = "https://data.police.uk/api/crime-last-updated"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                date_str = data.get('date', None)

                if date_str:
                    # Parse the date and ensure it's in YYYY-MM format
                    # The API might return YYYY-MM-DD or YYYY-MM format
                    if len(date_str) > 7:  # e.g., "2024-10-01"
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        return date_obj.strftime("%Y-%m")
                    else:  # Already in YYYY-MM format
                        return date_str
            return None
        except Exception as e:
            print(f"Error fetching last updated date: {e}")
            return None
    return (get_last_updated,)


@app.cell
def _(datetime):
    def generate_month_range(start_date="2022-10", end_date=None):
        """Generate list of all months from start_date to end_date in YYYY-MM format
        Default start date is 2022-10, which is when UK Police API data begins
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m")

        start = datetime.strptime(start_date, "%Y-%m")
        end = datetime.strptime(end_date, "%Y-%m")

        months = []
        current = start
        while current <= end:
            months.append(current.strftime("%Y-%m"))
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return months
    return (generate_month_range,)


@app.cell
def _(alt):
    def create_crime_histogram(crime_counts_df, current_month):
        """Create a histogram showing crime counts by month with current month highlighted"""
        if len(crime_counts_df) == 0:
            return alt.Chart().mark_text(text="No data available")

        # Add a column to indicate if this is the current month
        crime_counts_df = crime_counts_df.with_columns(
            (crime_counts_df['month'] == current_month).alias('is_current')
        )

        # Create the histogram (non-interactive)
        chart = (
            alt.Chart(crime_counts_df)
            .mark_bar()
            .encode(
                x=alt.X('month:N', title='Month', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('crimes_count:Q', title='Total Crimes'),
                color=alt.condition(
                    alt.datum.is_current == True,
                    alt.value('#e74c3c'),  # Red for current month
                    alt.value('#3498db')   # Blue for other months
                ),
                tooltip=[
                    alt.Tooltip('month:N', title='Month'),
                    alt.Tooltip('crimes_count:Q', title='Total Crimes', format=',')
                ]
            )
            .properties(
                height=150,  # Short height as requested
                width='container'  # Full width
            )
        )
        return chart
    return (create_crime_histogram,)


@app.cell
def _(folium):
    def create_crime_map(crimes_df, center_lat, center_lng):
        """Create an interactive Folium map with crime markers"""

        # Create map centered on the postcode location
        # Zoom level 14 gives approximately 2.5 mile x 2.5 mile view
        crime_map = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=14,
            tiles='OpenStreetMap',
            min_zoom=13,  # Prevent zooming out too far
            max_zoom=16   # Prevent zooming in too close
        )

        # Color mapping for crime categories
        category_colors = {
            'anti-social-behaviour': 'orange',
            'bicycle-theft': 'blue',
            'burglary': 'red',
            'criminal-damage-arson': 'darkred',
            'drugs': 'purple',
            'other-theft': 'lightblue',
            'possession-of-weapons': 'black',
            'public-order': 'pink',
            'robbery': 'darkpurple',
            'shoplifting': 'lightgreen',
            'theft-from-the-person': 'cadetblue',
            'vehicle-crime': 'darkblue',
            'violent-crime': 'darkred',
            'other-crime': 'gray'
        }

        # Add a marker for the center (postcode location)
        folium.Marker(
            location=[center_lat, center_lng],
            popup='Search Location',
            tooltip='Postcode Location',
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(crime_map)

        # Add crime markers
        for crime in crimes_df.iter_rows(named=True):
            color = category_colors.get(crime['category'], 'gray')

            folium.CircleMarker(
                location=[crime['lat'], crime['lng']],
                radius=6,
                popup=f"""
                    <b>Category:</b> {crime['category']}<br>
                    <b>Street:</b> {crime['street_name']}<br>
                    <b>Month:</b> {crime['month']}<br>
                    <b>Location:</b> {crime['lat']:.4f}, {crime['lng']:.4f}
                """,
                tooltip=crime['category'].replace('-', ' ').title(),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(crime_map)

        return crime_map
    return (create_crime_map,)


@app.cell
def _(requests, time):
    def fetch_crimes_at_location(lat, lng, date):
        """Fetch crimes at a specific location and date from UK Police API"""
        # Rate limiting: max 10 requests per second (100ms between requests)
        time.sleep(0.1)

        try:
            #url = "https://data.police.uk/api/crimes-at-location"
            url ="https://data.police.uk/api/crimes-street/all-crime"
            params = {
                'date': date,
                'lat': lat,
                'lng': lng
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                crimes = response.json()

                # Extract required fields
                processed_crimes = []
                for crime in crimes:
                    processed_crimes.append({
                        'id': crime.get('id', ''),
                        'category': crime.get('category', ''),
                        'month': crime.get('month', ''),
                        'lat': float(crime.get('location', {}).get('latitude', 0)),
                        'lng': float(crime.get('location', {}).get('longitude', 0)),
                        'street_name': crime.get('location', {}).get('street', {}).get('name', '')
                    })

                return processed_crimes
            else:
                print(f"API Error: Status {response.status_code}")
                return []

        except Exception as e:
            print(f"Error fetching crimes: {e}")
            return []
    return (fetch_crimes_at_location,)


@app.cell
def _(datetime, mo, timedelta):
    # UI inputs for postcode and date
    # Default date is last month
    last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")

    postcode_input = mo.ui.text(
        placeholder="Enter UK postcode (e.g., SW1A 1AA)",
        label="Postcode:"
    )

    date_input = mo.ui.text(
        value=last_month,
        placeholder="YYYY-MM",
        label="Date (Year-Month):"
    )

    submit_button = mo.ui.run_button(label="Fetch Crimes")

    mo.vstack([
        postcode_input,
        date_input,
        submit_button
    ])
    return date_input, postcode_input, submit_button


@app.cell
def _(
    add_to_query_cache,
    check_query_cache,
    create_crime_histogram,
    create_crime_map,
    date_input,
    fetch_crimes_at_location,
    generate_month_range,
    get_crime_counts_by_month,
    get_crimes_from_db_filtered,
    get_last_updated,
    init_database,
    mo,
    pl,
    postcode_input,
    postcode_to_coordinates,
    save_crimes_to_db,
    submit_button,
    validate_date_format,
):
    # Main processing logic
    result_message = None
    crimes_fetched = []
    db_path = init_database()

    # Track variables for this run only
    current_lat = None
    current_lng = None
    current_postcode = None
    successfully_processed = False

    if submit_button.value:
        # Check most recent data available
        last_updated = get_last_updated()

        postcode = postcode_input.value
        date = date_input.value

        # Validate date format first
        if date:
            is_valid, error_msg = validate_date_format(date, last_updated)
            if not is_valid:
                result_message = mo.md(f"❌ **Invalid date:** {error_msg}")
            elif not postcode:
                result_message = mo.md("Please enter a postcode.")
        elif postcode:
            result_message = mo.md("Please enter a date.")
        else:
            result_message = mo.md("Please enter both postcode and date.")

        if postcode and date and result_message is None:
            # Convert postcode to coordinates
            lat, lng = postcode_to_coordinates(postcode)

            if lat and lng:
                # Mark as successfully processed and update current variables
                successfully_processed = True
                current_lat = lat
                current_lng = lng
                current_postcode = postcode

                # Check cache first
                is_cached, cached_count, fetched_at = check_query_cache(db_path, postcode, date)

                if is_cached:
                    # Data already exists - retrieve from database (filtered by location)
                    crimes_df = get_crimes_from_db_filtered(db_path, date, lat, lng)
                    new_records = 0
                    data_source = "cache"

                    if len(crimes_df) > 0:
                        # Get crime counts by month for histogram (filtered by location)
                        crime_counts_df = get_crime_counts_by_month(db_path, postcode, lat, lng)

                        # Check if querying for future date
                        date_warning = ""
                        if last_updated and date > last_updated:
                            date_warning = f"\n\n⚠️ **Warning:** You're querying for {date}, but the most recent data available is {last_updated}. This query will return no results."

                        last_updated_text = f"**Most Recent Data Available:** {last_updated}" if last_updated else ""

                        # Create histogram and map
                        histogram_chart = create_crime_histogram(crime_counts_df, date)
                        crime_map = create_crime_map(crimes_df, lat, lng)

                        result_message = mo.vstack([
                            mo.md(f"""
                            ### Results ✓ (From Cache)
                            - **Postcode:** {postcode}
                            - **Coordinates:** {lat:.6f}, {lng:.6f}
                            - **Date:** {date}
                            - {last_updated_text}
                            - **Crimes Found:** {len(crimes_df)}
                            - **Data Source:** Cache (fetched {fetched_at})
                            - **New API Call:** No - data already in database
                            {date_warning}
                            """),
                            mo.md("### Crime Trends by Month"),
                            histogram_chart,
                            mo.md("### Interactive Map"),
                            crime_map
                        ])
                    else:
                        result_message = mo.md(f"Cache shows no crimes for this location and date (checked {fetched_at}).")
                else:
                    # Not cached - fetch from API
                    crimes_fetched = fetch_crimes_at_location(lat, lng, date)
                    data_source = "API"

                    if crimes_fetched:
                        # Save to database
                        new_records = save_crimes_to_db(crimes_fetched, db_path)

                        # Add to cache
                        add_to_query_cache(db_path, postcode, date, lat, lng, len(crimes_fetched))

                        # Convert to Polars DataFrame for map
                        crimes_df = pl.DataFrame(crimes_fetched)

                        # Check if querying for future date
                        date_warning = ""
                        if last_updated and date > last_updated:
                            date_warning = f"\n\n⚠️ **Warning:** You're querying for {date}, but the most recent data available is {last_updated}."

                        last_updated_text = f"**Most Recent Data Available:** {last_updated}" if last_updated else ""

                        # Create map first (show immediately while background fetching happens)
                        crime_map = create_crime_map(crimes_df, lat, lng)

                        # Display map first - histogram will be added after background fetching
                        result_message = mo.vstack([
                            mo.md(f"""
                            ### Results (Fresh from API)
                            - **Postcode:** {postcode}
                            - **Coordinates:** {lat:.6f}, {lng:.6f}
                            - **Date:** {date}
                            - {last_updated_text}
                            - **Crimes Found:** {len(crimes_fetched)}
                            - **New Records Added:** {new_records}
                            - **Data Source:** UK Police API (just fetched)
                            {date_warning}

                            *Fetching historical data in background...*
                            """),
                            mo.md("### Interactive Map"),
                            crime_map
                        ])
                    else:
                        # No crimes found - still add to cache so we don't query again
                        add_to_query_cache(db_path, postcode, date, lat, lng, 0)

                        # Check if querying for future date
                        date_info = ""
                        if last_updated and date > last_updated:
                            date_info = f" The most recent data available is {last_updated}."
                        elif last_updated:
                            date_info = f" (Most recent data available: {last_updated})"

                        result_message = mo.md(f"No crimes found for this location and date.{date_info}")
            else:
                result_message = mo.md("Invalid postcode. Please try again.")

        # Background fetching: populate database with all historical data for this location
        # Only run if we successfully processed a query in this run
        background_status = None
        histogram_after_fetch = None

        if successfully_processed and last_updated:
            # Generate all months from 2022-10 to most recent available (when UK Police API data begins)
            all_months = generate_month_range("2022-10", last_updated)

            # Filter out the month we just processed
            months_to_fetch = [m for m in all_months if m != date]

            # Count how many need fetching
            months_needing_fetch = []
            for month in months_to_fetch:
                is_cached, _, _ = check_query_cache(db_path, current_postcode, month)
                if not is_cached:
                    months_needing_fetch.append(month)

            if months_needing_fetch:
                # Fetch each missing month with progress tracking
                fetched_count = 0
                total_crimes_added = 0
                progress_updates = []

                for idx, month in enumerate(months_needing_fetch, 1):
                    crimes = fetch_crimes_at_location(current_lat, current_lng, month)
                    new_records = 0
                    if crimes:
                        new_records = save_crimes_to_db(crimes, db_path)
                        total_crimes_added += new_records
                    add_to_query_cache(db_path, current_postcode, month, current_lat, current_lng, len(crimes) if crimes else 0)
                    fetched_count += 1

                    # Progress tracking removed to prevent output size issues

                background_status = mo.md(f"✓ **Background fetch complete:** Fetched {fetched_count} months of historical data ({total_crimes_added:,} new crime records added to database).")

                # After background fetching, generate histogram with all the historical data
                # This only applies if we just fetched fresh data (not from cache)
                if 'data_source' in locals() and data_source == "API":
                    crime_counts_df = get_crime_counts_by_month(db_path, current_postcode, current_lat, current_lng)
                    histogram_after_fetch = create_crime_histogram(crime_counts_df, date)
            else:
                background_status = mo.md(f"✓ **Database up to date:** All months from 2022-10 to {last_updated} already cached for this location.")

                # Still generate histogram even if no fetching needed (data already exists)
                if 'data_source' in locals() and data_source == "API":
                    crime_counts_df = get_crime_counts_by_month(db_path, current_postcode, current_lat, current_lng)
                    histogram_after_fetch = create_crime_histogram(crime_counts_df, date)

    # Display the result
    if not result_message:
        display_msg = mo.md("Enter a postcode and date to fetch crime data.")
    elif histogram_after_fetch:
        # Fresh API fetch: add histogram after background fetching
        components = [result_message, mo.md("### Crime Trends by Month"), histogram_after_fetch]
        if background_status:
            components.append(background_status)
        display_msg = mo.vstack(components)
    elif background_status:
        # Cached query: add background status
        display_msg = mo.vstack([result_message, background_status])
    else:
        # No additional components
        display_msg = result_message

    # Display message
    mo.output.replace(display_msg)

    # Export variables for potential reactivity
    return


@app.cell
def _():
    # Histogram selection cell - REMOVED
    # The histogram is now non-interactive (no month selection via clicking)
    # It only displays crime trends with the submitted month highlighted in red
    return


if __name__ == "__main__":
    app.run()
