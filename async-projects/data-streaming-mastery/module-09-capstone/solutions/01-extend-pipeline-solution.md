# Solution: Exercise 1 - Returns Rate Metric

## 1. ksqlDB Query

Submit this query to ksqlDB (via REST API or add to `ksqldb-queries.sql`):

```sql
CREATE TABLE IF NOT EXISTS returns_rate
WITH (
    KAFKA_TOPIC = 'RETURNS_RATE',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 1
) AS
SELECT
    1 AS dummy_key,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) AS delivered_count,
    SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) AS returned_count,
    CASE
        WHEN (SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) +
              SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END)) > 0
        THEN CAST(
            SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) * 100.0 /
            (SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) +
             SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END))
            AS DOUBLE)
        ELSE 0.0
    END AS returns_rate_pct
FROM orders_stream
WINDOW TUMBLING (SIZE 15 MINUTES)
WHERE status IN ('delivered', 'returned')
GROUP BY 1
EMIT CHANGES;
```

**Explanation:**
- We filter to only `delivered` and `returned` statuses.
- `CASE WHEN` expressions count each status separately.
- The returns rate is `returned / (delivered + returned) * 100`.
- A `CASE` expression guards against division by zero.
- `1 AS dummy_key` is used because ksqlDB requires a GROUP BY key.

## 2. PostgreSQL Table

```sql
CREATE TABLE IF NOT EXISTS returns_rate (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    delivered_count INT,
    returned_count INT,
    returns_rate_pct DECIMAL(5,2),
    PRIMARY KEY (window_start, window_end)
);
```

## 3. Extend sink_consumer.py

Add this method to the `PostgresWriter` class:

```python
def upsert_returns_rate(self, records):
    """Upsert returns rate metric."""
    self._ensure_connected()
    sql = """
        INSERT INTO returns_rate
            (window_start, window_end, delivered_count, returned_count, returns_rate_pct)
        VALUES (%(window_start)s, %(window_end)s, %(delivered_count)s,
                %(returned_count)s, %(returns_rate_pct)s)
        ON CONFLICT (window_start, window_end) DO UPDATE SET
            delivered_count = EXCLUDED.delivered_count,
            returned_count = EXCLUDED.returned_count,
            returns_rate_pct = EXCLUDED.returns_rate_pct;
    """
    with self.conn.cursor() as cur:
        for r in records:
            params = {
                "window_start": _to_timestamp(r.get("WINDOW_START") or r.get("window_start")),
                "window_end": _to_timestamp(r.get("WINDOW_END") or r.get("window_end")),
                "delivered_count": r.get("DELIVERED_COUNT") or r.get("delivered_count"),
                "returned_count": r.get("RETURNED_COUNT") or r.get("returned_count"),
                "returns_rate_pct": r.get("RETURNS_RATE_PCT") or r.get("returns_rate_pct"),
            }
            cur.execute(sql, params)
    self.conn.commit()
```

Add to `TOPIC_TABLE_MAP`:
```python
"RETURNS_RATE": "returns_rate",
```

Add to `process_message()`:
```python
elif topic == "RETURNS_RATE":
    writer.upsert_returns_rate([value])
```

## 4. Grafana Panel

Add this panel to the dashboard JSON (or create via the Grafana UI):

```json
{
  "datasource": {
    "type": "postgres",
    "uid": "PostgreSQL Analytics"
  },
  "fieldConfig": {
    "defaults": {
      "thresholds": {
        "mode": "absolute",
        "steps": [
          { "color": "green", "value": null },
          { "color": "yellow", "value": 5 },
          { "color": "red", "value": 10 }
        ]
      },
      "unit": "percent",
      "min": 0,
      "max": 100
    }
  },
  "gridPos": { "h": 4, "w": 6, "x": 18, "y": 4 },
  "id": 9,
  "options": {
    "orientation": "auto",
    "reduceOptions": {
      "calcs": ["lastNotNull"],
      "fields": "",
      "values": false
    },
    "showThresholdLabels": false,
    "showThresholdMarkers": true
  },
  "title": "Returns Rate (%)",
  "type": "gauge",
  "targets": [
    {
      "datasource": {
        "type": "postgres",
        "uid": "PostgreSQL Analytics"
      },
      "editorMode": "code",
      "format": "table",
      "rawQuery": true,
      "rawSql": "SELECT returns_rate_pct AS \"Returns Rate\" FROM returns_rate ORDER BY window_start DESC LIMIT 1;",
      "refId": "A"
    }
  ]
}
```

## Verification

```bash
# Check the returns_rate table in PostgreSQL
docker exec -it module-09-postgres psql -U postgres -d analytics \
  -c "SELECT * FROM returns_rate ORDER BY window_start DESC LIMIT 5;"

# Expected output shows window periods with delivered/returned counts
# and the computed percentage.
```
