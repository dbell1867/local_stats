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
    from datetime import datetime, timedelta
    from pathlib import Path
    return Path, alt, datetime, mo, pl, requests, sqlite3, time, timedelta


@app.cell
def _(Path, sqlite3):
    def init_database():
        """Initialize SQLite database with crimes table"""
        db_path = Path("crimes.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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
                    alt.Tooltip(field='month')
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
    chart_crimes,
    date_input,
    fetch_crimes_at_location,
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
                # Fetch crimes from API
                crimes_fetched = fetch_crimes_at_location(lat, lng, date)

                if crimes_fetched:
                    # Save to database
                    new_records = save_crimes_to_db(crimes_fetched, db_path)

                    # Convert to Polars DataFrame for charting
                    crimes_df = pl.DataFrame(crimes_fetched)
                    chart = chart_crimes(crimes_df)

                    result_message = mo.vstack([
                        mo.md(f"""
                        ### Results
                        - **Postcode:** {postcode}
                        - **Coordinates:** {lat:.6f}, {lng:.6f}
                        - **Date:** {date}
                        - **Crimes Found:** {len(crimes_fetched)}
                        - **New Records Added:** {new_records}
                        """),
                        mo.ui.altair_chart(chart)
                    ])
                else:
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
