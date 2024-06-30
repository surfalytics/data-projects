# Spark ML Logs Transformer

Your first task as a newly hired data engineer is to implement
a simple ETL process on a logs stream, produced by data scientists
in their machine learning experiments.

## Data

Inside `app/logs.jsonl` you will find a part of this stream
in JSONL format, i.e. a single, valid JSON object per line.

The log object consists of the following fields:
* `logId` - a string-based unique indentifier,
* `expId` - an int-based identifier of the experiment, in which this log was produced,
* `metricId` - an int-based identifier of the metric, of which this log represents the value,
* `valid` - a deprecated boolean representing whether the log is valid or not (not used),
* `createdAt` - a date when the log was produced,
* `ingestedAt` - a date when the log was written to the stream,
* `step` - a consecutive identifier inside the experiment representing the order,
* `value` - a value of the metric.

You can find the corresponding experiments names in `app/experiments.csv` file.

On the other hand, metric names are well-known inside the company,
so you have to memorize them on your own: `0` means `Loss` and `1` is `Accuracy`.

## Tasks

Your task is to implement an ETL pipeline, which reads an input logs stream,
merges additional information, transforms the data and finally,
stores it in a new format.

### Part 1: Data loaders

In `app/etl.py` implement the following functions:
1. `load_logs` - it should accept a path to a JSONL file, as defined in the **Data** section above,
and returns a Spark `DataFrame` object containing logs data,
2. `load_experiments` - it should accept a path to a CSV file and
returns a Spark `DataFrame` object containing `expId` and `expName` columns,
3. `load_metrics` - it should returns a Spark `DataFrame` object containing two rows and two columns,
as defined in the **Data** section above.

### Part 2: Merge data sources

Having the data loaded, your task is to merge the results into a single `DataFrame`.
Implement `join_tables` function which accepts `DataFrame`s from the previous task,
and returns a new `DataFrame` with all three tables merged, using `expId` and `metricId`
as foreign keys.

### Part 3: Filter invalid logs

Some of the logs were ingested into the stream too late. We don't want that kind of behavior,
and your task is to filter out logs, which were injected later than some specified number
of hours after the creation date. Implement `filter_late_logs` method.

### Part 4: Calculate experiment's statistics

Once you filtered out invalid logs, your task is to calculate final metrics for each
metric in each experiment. The final metric value consists of the `min` and `max` values
for each metric in each experiment. The expected `DataFrame` should consists of
at least following columns:
* `expName` - name of the experiment,
* `metricName` - name of the metric,
* `maxValue` - max `value` of the `metricName` in the `expName`,
* `minValue` - min `value` of the `metricName` in the `expName`.

### Part 5: Save transformed data

Finally, the calculated statistics have to be saved in Parquet format.
Ideally, the data should be partitioned by `metricId` column, so the analysis of the
statistics in the future will be more efficient.

## Hints

To execute the unit tests, use:

```
pip install -q -e . && python3 setup.py pytest
```
