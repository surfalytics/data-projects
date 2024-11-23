# URL for NYC Taxi data (2023 Yellow Taxi Trip Data)
PARQUET_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"

print("Downloading NYC Taxi data...")

# Download the file to a temporary location
response = requests.get(PARQUET_URL)

# Create a temporary file
with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
    tmp_file.write(response.content)
    tmp_path = tmp_file.name

print("Reading Parquet file...")
table = pq.read_table(tmp_path, columns=[
    'tpep_pickup_datetime',
    'tpep_dropoff_datetime',
    'passenger_count',
    'trip_distance',
    'fare_amount',
    'tip_amount',
    'total_amount'
])

print(f"\nLoaded {len(table)} rows")

# Perform analysis using PyArrow compute functions

# 1. Basic Statistics
avg_fare = pc.mean(table['fare_amount'])
avg_distance = pc.mean(table['trip_distance'])
avg_tip = pc.mean(table['tip_amount'])
total_passengers = pc.sum(table['passenger_count'])

print("\nBasic Statistics:")
print(f"Average Fare: ${avg_fare.as_py():.2f}")
print(f"Average Distance: {avg_distance.as_py():.2f} miles")
print(f"Average Tip: ${avg_tip.as_py():.2f}")
print(f"Total Passengers: {total_passengers.as_py():,}")

# 2. Calculate trip duration in minutes
duration = pc.divide(
    pc.cast(
        pc.subtract(
            table['tpep_dropoff_datetime'],
            table['tpep_pickup_datetime']
        ),
        pa.int64()
    ),
    60
)

avg_duration = pc.mean(duration)
print(f"Average Trip Duration: {avg_duration.as_py():.1f} minutes")

# 3. Filter for interesting insights

# Long trips (>10 miles)
long_trips = table.filter(pc.greater(table['trip_distance'], 10))

# High tips (>20% of fare)
tip_percentage = pc.multiply(
    pc.divide(table['tip_amount'], table['fare_amount']),
    100
)
high_tips = table.filter(pc.greater(tip_percentage, 20))

print("\nInteresting Insights:")
print(f"Number of long trips (>10 miles): {len(long_trips)}")
print(f"Number of high tip trips (>20%): {len(high_tips)}")

# Memory usage information
memory_usage = table.nbytes / (1024 * 1024)  # Convert to MB
print(f"\nMemory Usage: {memory_usage:.2f} MB")