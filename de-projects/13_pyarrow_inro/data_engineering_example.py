import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Case 1: ETL Pipeline with Data Validation
def etl_pipeline_example():
    # Simulate raw data ingestion
    raw_data = {
        'user_id': [1, 2, 3, None, 5],
        'timestamp': [datetime.now() - timedelta(days=i) for i in range(5)],
        'amount': [100.50, -200.75, 300.25, 400.00, None],
        'status': ['completed', 'pending', 'failed', None, 'completed']
    }
    
    # Convert to Arrow Table
    table = pa.Table.from_pydict(raw_data)
    
    # Data Validation and Cleaning
    # 1. Check for nulls
    null_counts = {
        col: pc.sum(pc.is_null(table[col])).as_py()
        for col in table.column_names
    }
    
    # 2. Data type validation
    valid_amounts = pc.is_finite(table['amount'])
    valid_statuses = pc.is_in(table['status'], value_set=pa.array(['completed', 'pending', 'failed']))
    
    # 3. Apply business rules
    valid_rows = pc.and_(
        pc.is_valid(table['user_id']),
        valid_amounts,
        valid_statuses
    )
    
    # Filter and transform data
    clean_table = table.filter(valid_rows)
    
    print("Data Quality Report:")
    print(f"Original rows: {len(table)}")
    print(f"Clean rows: {len(clean_table)}")
    print(f"Null counts: {null_counts}")

# Case 2: Partitioned Dataset Management
def partitioned_dataset_management():
    # Create sample time-series data
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='H')
    data = {
        'timestamp': dates,
        'metric': np.random.randn(len(dates)),
        'category': np.random.choice(['A', 'B', 'C'], len(dates)),
        'region': np.random.choice(['EU', 'US', 'ASIA'], len(dates))
    }
    table = pa.Table.from_pydict(data)
    
    # Write partitioned dataset
    partition_schema = ds.partitioning(
        pa.schema([
            ('region', pa.string()),
            ('category', pa.string())
        ])
    )
    
    ds.write_dataset(
        table,
        'partitioned_data',
        format='parquet',
        partitioning=partition_schema
    )
    
    # Read specific partition
    dataset = ds.dataset('partitioned_data', partitioning=partition_schema)
    eu_data = dataset.scanner(
        filter=ds.field('region') == 'EU'
    ).to_table()
    
    print("\nPartitioned Dataset Info:")
    print(f"Total partitions: {len(list(dataset.files))}")
    print(f"EU region rows: {len(eu_data)}")

# Case 3: Performance Optimization for Large Data Processing
def optimize_large_data_processing():
    # Create large dataset
    n_rows = 1_000_000
    data = {
        'id': range(n_rows),
        'value': np.random.randn(n_rows),
        'category': np.random.choice(['X', 'Y', 'Z'], n_rows),
        'timestamp': [datetime.now() for _ in range(n_rows)]
    }
    
    # Convert to Arrow with chunking
    chunk_size = 250_000
    chunks = []
    
    for i in range(0, n_rows, chunk_size):
        chunk_data = {
            key: value[i:i+chunk_size] 
            for key, value in data.items()
        }
        chunks.append(pa.Table.from_pydict(chunk_data))
    
    # Process in parallel using Arrow compute functions
    table = pa.concat_tables(chunks)
    
    # Demonstrate aggregations
    result = {
        'mean': pc.mean(table['value']).as_py(),
        'count_by_category': pc.value_counts(table['category']).to_pydict(),
        'memory_usage_mb': table.nbytes / (1024 * 1024)
    }
    
    print("\nLarge Data Processing Results:")
    print(f"Memory usage: {result['memory_usage_mb']:.2f} MB")
    print(f"Mean value: {result['mean']:.2f}")
    print(f"Category counts: {result['count_by_category']}")

# Case 4: Data Format Conversion Pipeline
def format_conversion_pipeline():
    # Create sample data
    data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=1000),
        'values': np.random.randn(1000),
        'category': np.random.choice(['A', 'B', 'C'], 1000)
    })
    
    # Convert to different formats using Arrow as intermediate
    table = pa.Table.from_pandas(data)
    
    # Write to various formats
    pq.write_table(table, 'data.parquet', compression='snappy')
    feather_path = 'data.feather'
    pa.feather.write_feather(table, feather_path)
    
    # Read back and verify
    parquet_table = pq.read_table('data.parquet')
    feather_table = pa.feather.read_table(feather_path)
    
    print("\nFormat Conversion Results:")
    print(f"Original rows: {len(table)}")
    print(f"Parquet rows: {len(parquet_table)}")
    print(f"Feather rows: {len(feather_table)}")

if __name__ == "__main__":
    etl_pipeline_example()
    partitioned_dataset_management()
    optimize_large_data_processing()
    format_conversion_pipeline()