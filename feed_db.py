import sqlite3
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from faker import Faker

# --------------------------------------------------
# Configuration
# --------------------------------------------------

DB_PATH = "arkagents.db"
TABLE_NAME = "customer"
RECORD_COUNT = 1000

fake = Faker()

# Agent IDs
AGENT_IDS = [
    101, 102, 103, 104, 105,
    106, 107, 108, 109, 110
]

# Possible destinations
DESTINATIONS = [
    "Dubai",
    "Singapore",
    "Bali",
    "Thailand",
    "Maldives",
    "Paris",
    "London",
    "Switzerland",
    "New York",
    "Tokyo",
    "Australia",
    "Malaysia",
    "Mauritius",
    "Vietnam",
    "Sri Lanka",
    "Indonesia",
    "Italy",
    "Spain",
    "Greece",
    "Turkey",
]

# Booking dates between these dates
START_BOOKING_DATE = datetime(2024, 1, 1)
END_BOOKING_DATE = datetime(2026, 6, 30)

# --------------------------------------------------
# Connect to SQLite
# --------------------------------------------------

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# --------------------------------------------------
# Get the next available booking_id
# --------------------------------------------------

cursor.execute(
    f"SELECT COALESCE(MAX(booking_id), 0) FROM {TABLE_NAME}"
)

last_booking_id = cursor.fetchone()[0]

# --------------------------------------------------
# Generate records
# --------------------------------------------------

records = []

booking_date_range = (
    END_BOOKING_DATE - START_BOOKING_DATE
).days

for i in range(1, RECORD_COUNT + 1):

    booking_id = last_booking_id + i

    # Random agent
    agent_id = random.choice(AGENT_IDS)

    # Number of passengers
    no_of_pax = random.randint(1, 10)

    # --------------------------------------------------
    # Booking date
    # --------------------------------------------------

    booking_date = START_BOOKING_DATE + timedelta(
        days=random.randint(0, booking_date_range)
    )

    # --------------------------------------------------
    # Travel date
    #
    # Minimum = 2 calendar months after booking date
    # Maximum = approximately 6 months after booking date
    # --------------------------------------------------

    min_travel_date = booking_date + relativedelta(months=2)

    travel_date = min_travel_date + timedelta(
        days=random.randint(0, 120)
    )

    # --------------------------------------------------
    # Destination
    # --------------------------------------------------

    destination = random.choice(DESTINATIONS)

    # --------------------------------------------------
    # Total price
    #
    # Generate a realistic price based on pax.
    # --------------------------------------------------

    price_per_person = random.uniform(400, 2500)

    total_price = round(
        price_per_person * no_of_pax,
        2
    )

    # --------------------------------------------------
    # Add record
    # --------------------------------------------------

    records.append(
        (
            booking_id,
            agent_id,
            no_of_pax,
            booking_date.strftime("%Y-%m-%d"),
            travel_date.strftime("%Y-%m-%d"),
            destination,
            total_price,
        )
    )

# --------------------------------------------------
# Insert records
# --------------------------------------------------

cursor.executemany(
    f"""
    INSERT INTO {TABLE_NAME} (
        booking_id,
        agent_id,
        no_of_pax,
        booking_date,
        travel_date,
        destination,
        total_price
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    records,
)

conn.commit()

# --------------------------------------------------
# Verification
# --------------------------------------------------

cursor.execute(
    f"SELECT COUNT(*) FROM {TABLE_NAME}"
)

total_records = cursor.fetchone()[0]

print(f"Successfully inserted {RECORD_COUNT} records.")
print(f"Total records in {TABLE_NAME}: {total_records}")

# --------------------------------------------------
# Verify travel-date rule
# --------------------------------------------------

cursor.execute(
    f"""
    SELECT COUNT(*)
    FROM {TABLE_NAME}
    WHERE date(travel_date) < date(booking_date, '+2 months')
    """
)

invalid_records = cursor.fetchone()[0]

if invalid_records == 0:
    print("✓ All travel dates are at least 2 months after booking dates.")
else:
    print(
        f"⚠ Found {invalid_records} records "
        "that violate the 2-month travel-date rule."
    )

conn.close()

print("Database connection closed.")