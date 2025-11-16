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
    return Path, alt, datetime, folium, mo, pl, requests, sqlite3, time, timedelta


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
    def get_crimes_from_db_filtered(db_path, month):
        """Retrieve crimes from database for a specific month"""
        conn = sqlite3.connect(db_path)

        df = pl.read_database(
            "SELECT * FROM crimes WHERE month = ?",
            connection=conn,
            execute_options={"parameters": (month,)}
        )

        conn.close()
        return df
    return (get_crimes_from_db_filtered,)


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
def _(alt):
    def chart_crimes(crimes_fetched):
        chart = (
            alt.Chart(crimes_fetched)
            .mark_point()
            .encode(
                x=alt.X(field='lng', type='quantitative').scale(zero=False),
                y=alt.Y(field='lat', type='quantitative').scale(zero=False),
                color=alt.Color(field='category', type='nominal'),
                tooltip=[
                    alt.Tooltip(field='lat', format=',.2f'),
                    alt.Tooltip(field='lng', format=',.2f'),
                    alt.Tooltip(field='street_name')
                ]
            )
            .properties(
                height=290,
                width='container',
                config={
                    'axis': {
                        'grid': True
                    }
                }
            )
        )
        return chart
    return (chart_crimes,)


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
    chart_crimes,
    check_query_cache,
    create_crime_map,
    date_input,
    fetch_crimes_at_location,
    get_crimes_from_db_filtered,
    init_database,
    mo,
    pl,
    postcode_input,
    postcode_to_coordinates,
    save_crimes_to_db,
    submit_button,
):
    # Main processing logic
    result_message = None
    crimes_fetched = []
    db_path = init_database()

    if submit_button.value:
        postcode = postcode_input.value
        date = date_input.value

        if postcode and date:
            # Convert postcode to coordinates
            lat, lng = postcode_to_coordinates(postcode)

            if lat and lng:
                # Check cache first
                is_cached, cached_count, fetched_at = check_query_cache(db_path, postcode, date)

                if is_cached:
                    # Data already exists - retrieve from database
                    crimes_df = get_crimes_from_db_filtered(db_path, date)
                    new_records = 0
                    data_source = "cache"

                    if len(crimes_df) > 0:
                        chart = chart_crimes(crimes_df)
                        crime_map = create_crime_map(crimes_df, lat, lng)

                        result_message = mo.vstack([
                            mo.md(f"""
                            ### Results ✓ (From Cache)
                            - **Postcode:** {postcode}
                            - **Coordinates:** {lat:.6f}, {lng:.6f}
                            - **Date:** {date}
                            - **Crimes Found:** {len(crimes_df)}
                            - **Data Source:** Cache (fetched {fetched_at})
                            - **New API Call:** No - data already in database
                            """),
                            mo.md("### Interactive Map"),
                            crime_map,
                            mo.md("### Crime Distribution Chart"),
                            mo.ui.altair_chart(chart)
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

                        # Convert to Polars DataFrame for charting
                        crimes_df = pl.DataFrame(crimes_fetched)
                        chart = chart_crimes(crimes_df)
                        crime_map = create_crime_map(crimes_df, lat, lng)

                        result_message = mo.vstack([
                            mo.md(f"""
                            ### Results (Fresh from API)
                            - **Postcode:** {postcode}
                            - **Coordinates:** {lat:.6f}, {lng:.6f}
                            - **Date:** {date}
                            - **Crimes Found:** {len(crimes_fetched)}
                            - **New Records Added:** {new_records}
                            - **Data Source:** UK Police API (just fetched)
                            """),
                            mo.md("### Interactive Map"),
                            crime_map,
                            mo.md("### Crime Distribution Chart"),
                            mo.ui.altair_chart(chart)
                        ])
                    else:
                        # No crimes found - still add to cache so we don't query again
                        add_to_query_cache(db_path, postcode, date, lat, lng, 0)
                        result_message = mo.md("No crimes found for this location and date.")
            else:
                result_message = mo.md("Invalid postcode. Please try again.")
        else:
            result_message = mo.md("Please enter both postcode and date.")

    # Display the result
    display_msg = result_message if result_message else mo.md("Enter a postcode and date to fetch crime data.")

    # Return db_path for use in other cells, and display message
    mo.output.replace(display_msg)

    print(submit_button.value)
    return


if __name__ == "__main__":
    app.run()
