# What is PyArrow

PyArrow is like a super-fast data handling tool that helps you work with large amounts of data efficiently. Think of it as a high-speed train for your data compared to regular Python's local bus service.

> The Arrow columnar format includes a language-agnostic in-memory data structure specification, metadata serialization, and a protocol for serialization and generic data transport. It provides analytical performance and data locality guarantees in exchange for comparatively more expensive mutation operations.

Key Benefits of PyArrow:
- Speed: Much faster than regular Python for data operations
- Memory efficiency: Uses less RAM
- Compatibility: Works well with other data tools
- Handles complex data types easily

1. Working with Large Datasets:
   - When handling files > 1GB
   - When you need better memory efficiency
   - When processing speed is important

2. Working with Parquet Files:
   - When you need to read/write Parquet format (common in big data)
   - When working with data warehouses
   - When you need efficient data storage

3. Data Type Precision:
   - When you need exact control over data types
   - When working with timestamps and decimals
   - When data type consistency is crucial

4. Big Data Integration:
   - When working with Apache Spark
   - When connecting to data lakes
   - When using big data tools

5. Specific Use Cases Where PyArrow Shines:
   - ETL (Extract, Transform, Load) pipelines
   - Data warehousing operations
   - Real-time data processing
   - Cross-platform data exchange

You DON'T need PyArrow when:
- Working with small datasets (< 100MB)
- Doing simple data analysis
- Working with simple CSV files
- No need for high performance


Reference:
- [Arrow Columnar Format Documentation](https://arrow.apache.org/docs/format/Columnar.html)
- [An analysis of the strengths and weaknesses of Apache Arrow](https://dbmsmusings.blogspot.com/2018/03/an-analysis-of-strengths-and-weaknesses.html)
- [Apache Arrow: Overview](https://vutr.substack.com/p/i-spent-6-hours-learning-apache-arrow)


# Hands-On

## Install Poetry

```bash
pipx install poetry
export PATH="$HOME/.local/bin:$PATH"

cd de-projects/13_pyarrow_inro  

# isntall
poetry install

# activate
poetry shell

python3 ny_tax_parquet.py
```