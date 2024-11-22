import pyarrow as pa
import pyarrow.dataset as ds
import pandas as pd
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table
import pyiceberg.catalog.hive
from datetime import datetime

def demonstrate_arrow_pandas_integration():
    # Create pandas DataFrame
    pdf = pd.DataFrame({
        'id': range(1000),
        'timestamp': [datetime.now() for _ in range(1000)],
        'values': range(1000)
    })
    
    # Convert Pandas to Arrow
    arrow_table = pa.Table.from_pandas(pdf)
    
    # Convert back to Pandas
    pdf_back = arrow_table.to_pandas()
    
    print("Arrow-Pandas Integration:")
    print(f"Original Pandas shape: {pdf.shape}")
    print(f"Arrow Table shape: {len(arrow_table), len(arrow_table.columns)}")
    print(f"Converted back to Pandas shape: {pdf_back.shape}")

if __name__ == "__main__":
    demonstrate_arrow_pandas_integration()  