# Getting Started with Polars

Polars is a high-performance DataFrame library for data manipulation and analysis in Python. Here are the key highlights:

What is Polars?

- A modern data processing library written in Rust
- Leverages Apache Arrow for high-performance data manipulation
- Designed to be faster and more memory-efficient than Pandas
- Supports lazy execution and function chaining
- Similar naming conventions to PySpark
- Uses parallelism and Apache Arrow for speed improvements

Key Advantages of Polars:

1. **Performance**
   - Significantly faster than Pandas (users report 5-10x speedups)
   - Utilizes all CPU cores efficiently
   - Memory-efficient due to Rust implementation
   - Supports lazy evaluation and optimization by default

2. **Key Features**
   - Easy installation (minimal dependencies)
   - Intuitive API similar to dplyr in R
   - Supports out-of-core computation in lazy mode
   - Good for data wrangling and well-defined data pipelines

### Comparison with Other Libraries

Pandas:

- More feature-rich and mature
- Better for financial/physical modeling and complex cross-frame operations
- Slower and less memory-efficient
- Originally designed for data analysts and Excel users

PyArrow:

- A data processing library focusing on file formats and memory representation
- Polars uses Apache Arrow as its underlying technology
- Helps with efficient data serialization and memory management

PySpark:

- Designed for distributed computing and big data processing
- Excellent for datasets larger than machine memory
- Overhead and complexity for smaller datasets
- Better for terabyte/petabyte scale data processing

### When to Use Polars

- Single-machine data processing
- Datasets that fit in memory
- Performance-critical data pipelines
- Data wrangling and transformation tasks
- When you want faster, more memory-efficient data manipulation

### Limitations

- Fewer features compared to Pandas
- Not ideal for very complex modeling scenarios
- Limited support for partitioned parquet files (but improving)

### Example

```python
import polars as pl

# Read a CSV
df = pl.read_csv('data.csv')

# Transform data
result = (df
    .filter(pl.col('value') > 10)
    .groupby('category')
    .agg(pl.sum('value'))
)
```

### Polars and PyArrow

PyArrow:

- Primarily a library for working with Apache Arrow file formats
- Focuses on efficient data serialization and memory representation
- Provides tools for reading/writing columnar data formats
- Not a full data manipulation library
- Mainly handles data storage and interchange

Polars: 

- A full-featured DataFrame library for data manipulation
- Built on top of Apache Arrow
- Provides comprehensive data processing capabilities
- Designed for performance and efficiency
- Supports complex data transformations, filtering, aggregations

Relationship Between Them:

- Polars uses Apache Arrow as its underlying technology
- You can convert between PyArrow and Polars DataFrames
- PyArrow is more about data format and memory efficiency
- Polars is about actual data processing and analysis

Instead of using PyArrow for computation, you might:

1. Use PyArrow to read/write efficient data formats
2. Convert to Polars for data manipulation
3. Potentially convert back to PyArrow or another format if needed

Example:
```python
import pyarrow.parquet as pq
import polars as pl

# Read parquet with PyArrow
arrow_table = pq.read_table('data.parquet')

# Convert to Polars for processing
polars_df = pl.from_arrow(arrow_table)

# Do data processing in Polars
result = polars_df.filter(pl.col('value') > 10)
```

#### Example with PARQUET file

Requires:

```bash
pip install pyarrow polars requests
```

```python
import pyarrow.parquet as pq
import polars as pl
import pyarrow as pa
import requests

# URL of the Parquet file
PARQUET_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"

# Download the Parquet file
def download_parquet_file(url, filename='yellow_tripdata_2023-01.parquet'):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)
    return filename

# Read Parquet file with PyArrow
def read_with_pyarrow(filename):
    # Read the entire Parquet file into a PyArrow Table
    arrow_table = pq.read_table(filename)
    return arrow_table

# Process with Polars
def process_with_polars(arrow_table):
    # Convert PyArrow Table to Polars DataFrame
    polars_df = pl.from_arrow(arrow_table)
    
    # Example processing: Filter trips longer than 10 miles
    long_trips = polars_df.filter(
        (pl.col('trip_distance') > 10) & 
        (pl.col('total_amount') > 50)
    )
    
    # Calculate some statistics
    stats = long_trips.group_by('PULocationID').agg([
        pl.col('trip_distance').mean().alias('avg_distance'),
        pl.col('total_amount').mean().alias('avg_total_amount'),
        pl.count().alias('trip_count')
    ])
    
    return stats

def main():
    # Download the file
    filename = download_parquet_file(PARQUET_URL)
    
    # Read with PyArrow
    arrow_table = read_with_pyarrow(filename)
    
    # Process with Polars
    result = process_with_polars(arrow_table)
    
    # Display results
    print(result)

if __name__ == "__main__":
    main()
```

The key steps are:

`pq.read_table()` reads the Parquet file
`pl.from_arrow()` converts the PyArrow Table to a Polars DataFrame

#### Example with only Polars

```python
import polars as pl
import requests

# URL of the Parquet file
PARQUET_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"

# Download the Parquet file
def download_parquet_file(url, filename='yellow_tripdata_2023-01.parquet'):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)
    return filename

def read_and_process_parquet():
    # Download the file
    filename = download_parquet_file(PARQUET_URL)
    
    # Read Parquet file directly with Polars
    # Option 1: Read entire file into memory
    df = pl.read_parquet(filename)
    
    # Option 2: Lazy reading (for larger files)
    # df = pl.scan_parquet(filename)
    
    # Example processing: Filter and aggregate
    long_trips = df.filter(
        (pl.col('trip_distance') > 10) & 
        (pl.col('total_amount') > 50)
    )
    
    # Calculate statistics by pickup location
    location_stats = long_trips.group_by('PULocationID').agg([
        pl.col('trip_distance').mean().alias('avg_distance'),
        pl.col('total_amount').mean().alias('avg_total_amount'),
        pl.count().alias('trip_count')
    ])
    
    # Sort by number of trips in descending order
    result = location_stats.sort('trip_count', descending=True)
    
    return result

# Run the function and print results
print(read_and_process_parquet())
```

Polars offers two main ways to read Parquet files:

`pl.read_parquet()`: Reads entire file into memory
`pl.scan_parquet()`: Lazy reading (better for large files)

The advantages of using Polars directly:

- Simpler code
- Native performance optimizations
- Integrated lazy execution
- Less dependency juggling
