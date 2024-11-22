import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Scenario 1: Large Dataset Handling
# When you have huge CSV files (>1GB)
def demonstrate_large_file_handling():
    # Create sample large dataset
    large_df = pd.DataFrame({
        'id': range(1_000_000),
        'value': np.random.randn(1_000_000),
        'category': np.random.choice(['A', 'B', 'C'], 1_000_000)
    })
    
    # Compare memory usage: Pandas vs PyArrow
    pandas_memory = large_df.memory_usage().sum() / 1024**2  # MB
    arrow_table = pa.Table.from_pandas(large_df)
    arrow_memory = arrow_table.nbytes / 1024**2  # MB
    
    print(f"Memory Usage Comparison:")
    print(f"Pandas: {pandas_memory:.2f} MB")
    print(f"PyArrow: {arrow_memory:.2f} MB")

# Scenario 2: Parquet File Operations
# When you need to work with Parquet files (common in big data)
def demonstrate_parquet_operations():
    # Create sample data
    data = {
        'date': [datetime.now() for _ in range(1000)],
        'values': np.random.randn(1000),
        'categories': np.random.choice(['X', 'Y', 'Z'], 1000)
    }
    df = pd.DataFrame(data)
    
    # Write to Parquet using PyArrow (faster than pandas)
    start_time = time.time()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, 'data_arrow.parquet')
    arrow_time = time.time() - start_time
    
    # Write to Parquet using pandas
    start_time = time.time()
    df.to_parquet('data_pandas.parquet')
    pandas_time = time.time() - start_time
    
    print(f"\nParquet Write Time Comparison:")
    print(f"PyArrow: {arrow_time:.4f} seconds")
    print(f"Pandas: {pandas_time:.4f} seconds")

# Scenario 3: Data Type Preservation
# When you need precise control over data types
def demonstrate_data_type_preservation():
    # Create data with specific types
    data = {
        'int32_col': pa.array([1, 2, 3], type=pa.int32()),
        'decimal_col': pa.array([1.23, 4.56, 7.89], type=pa.decimal128(5, 2)),
        'timestamp_col': pa.array([datetime.now()], type=pa.timestamp('ns'))
    }
    table = pa.Table.from_pydict(data)
    
    print("\nPrecise Data Types:")
    print(table.schema)

# Scenario 4: Integration with Big Data Tools
# When working with big data ecosystem (Spark, Hadoop)
def demonstrate_big_data_integration():
    # Create sample dataset
    data = {
        'id': range(100),
        'values': np.random.randn(100),
        'timestamp': [datetime.now() for _ in range(100)]
    }
    
    # Convert to Arrow format (ready for big data systems)
    table = pa.Table.from_pydict(data)
    
    # Write to Parquet with partitioning (common in big data)
    pq.write_table(table, 'big_data_example',
                   partition_cols=['id'])
    
    print("\nBig Data Integration:")
    print("Created partitioned dataset ready for big data systems")

# Run demonstrations
if __name__ == "__main__":
    demonstrate_large_file_handling()
    demonstrate_parquet_operations()
    demonstrate_data_type_preservation()
    demonstrate_big_data_integration()