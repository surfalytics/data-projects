import pyarrow as pa
import pandas as pd
import numpy as np
from datetime import datetime

# Basic Example 1: Creating a simple Arrow array
basic_array = pa.array([1, 2, 3, 4, 5])
print("Basic Array:", basic_array)

# Basic Example 2: Creating an Arrow table from a dictionary
data = {
    'numbers': [1, 2, 3, 4],
    'letters': ['a', 'b', 'c', 'd']
}
table = pa.Table.from_pydict(data)
print("\nSimple Table:\n", table)

# Intermediate Example 1: Working with different data types
structured_data = {
    'integers': [1, 2, 3],
    'floats': [1.1, 2.2, 3.3],
    'strings': ['one', 'two', 'three'],
    'dates': [datetime.now() for _ in range(3)],
    'booleans': [True, False, True]
}
structured_table = pa.Table.from_pydict(structured_data)
print("\nStructured Table Schema:\n", structured_table.schema)

# Intermediate Example 2: Converting between Pandas and Arrow
# Create a pandas DataFrame
df = pd.DataFrame({
    'id': range(1000),
    'values': np.random.randn(1000),
    'category': np.random.choice(['A', 'B', 'C'], 1000)
})

# Convert to Arrow Table and back
arrow_table = pa.Table.from_pandas(df)
df_back = arrow_table.to_pandas()

# Advanced Example 1: Custom Schema and Nested Data
nested_schema = pa.schema([
    ('id', pa.int32()),
    ('name', pa.string()),
    ('metrics', pa.struct([
        ('score', pa.float64()),
        ('confidence', pa.float64())
    ])),
    ('tags', pa.list_(pa.string()))
])

nested_data = [
    {
        'id': 1,
        'name': 'John',
        'metrics': {'score': 0.85, 'confidence': 0.92},
        'tags': ['expert', 'verified']
    },
    {
        'id': 2,
        'name': 'Jane',
        'metrics': {'score': 0.92, 'confidence': 0.88},
        'tags': ['newcomer']
    }
]

# Create arrays for each field
arrays = [
    pa.array([row['id'] for row in nested_data]),
    pa.array([row['name'] for row in nested_data]),
    pa.StructArray.from_pandas([row['metrics'] for row in nested_data]),
    pa.array([row['tags'] for row in nested_data])
]

# Create table with custom schema
nested_table = pa.Table.from_arrays(arrays, schema=nested_schema)
print("\nNested Table Schema:\n", nested_table.schema)

# Advanced Example 2: Memory Management and Chunked Arrays
# Create a large dataset
large_data = {
    'id': range(1_000_000),
    'value': np.random.randn(1_000_000)
}

# Convert to Arrow using chunks
chunk_size = 250_000
chunks = []
for i in range(0, 1_000_000, chunk_size):
    chunk_data = {
        'id': large_data['id'][i:i+chunk_size],
        'value': large_data['value'][i:i+chunk_size]
    }
    chunks.append(pa.Table.from_pydict(chunk_data))

# Combine chunks into a single table
chunked_table = pa.concat_tables(chunks)
print("\nChunked Table Info:")
print(f"Number of rows: {len(chunked_table)}")
print(f"Number of chunks: {chunked_table.column('id').num_chunks}")