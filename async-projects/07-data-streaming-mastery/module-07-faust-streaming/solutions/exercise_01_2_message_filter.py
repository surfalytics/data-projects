"""
Solution: Exercise 1.2 -- Message Filter Agent.

A Faust agent that reads sensor readings and routes them to different
output topics based on temperature thresholds. High-temperature readings
go to an alerts topic; normal readings go to a separate topic.

Usage:
    faust -A solutions.exercise_01_2_message_filter worker -l info

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class SensorReading(faust.Record):
    """A sensor reading event.

    Attributes:
        sensor_id: Unique identifier for the sensor.
        temperature: Temperature reading in Celsius.
        humidity: Humidity reading as a percentage.
        timestamp: When the reading was taken.
    """

    sensor_id: str
    temperature: float
    humidity: float
    timestamp: datetime


# ---------------------------------------------------------------------------
# App, Topics, Tables
# ---------------------------------------------------------------------------

app = faust.App(
    "message-filter-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

sensor_topic = app.topic("sensor-readings", value_type=SensorReading, partitions=4)
high_temp_topic = app.topic("high-temp-alerts", value_type=SensorReading, partitions=4)
normal_topic = app.topic("normal-readings", value_type=SensorReading, partitions=4)

# Table to track alert counts
alert_counter = app.Table("alert-counter", default=int)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

TEMP_THRESHOLD = 35.0


@app.agent(sensor_topic)
async def filter_readings(stream):
    """Route sensor readings based on temperature threshold.

    Readings with temperature > 35.0 C are sent to the high-temp-alerts topic.
    All other readings are sent to the normal-readings topic.
    """
    async for reading in stream:
        if reading.temperature > TEMP_THRESHOLD:
            await high_temp_topic.send(value=reading)
            print(
                f"[ALERT] sensor={reading.sensor_id} "
                f"temp={reading.temperature:.1f}C > {TEMP_THRESHOLD}C"
            )
        else:
            await normal_topic.send(value=reading)
            print(
                f"[NORMAL] sensor={reading.sensor_id} "
                f"temp={reading.temperature:.1f}C"
            )


@app.agent(high_temp_topic)
async def count_alerts(stream):
    """Count high-temperature alerts and print the running total."""
    async for reading in stream:
        alert_counter["total"] += 1
        alert_counter[reading.sensor_id] += 1
        print(
            f"[ALERT COUNT] total={alert_counter['total']} "
            f"sensor {reading.sensor_id}={alert_counter[reading.sensor_id]}"
        )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/alerts/")
async def alert_stats(web, request):
    """Return alert counts."""
    counts = {k: v for k, v in alert_counter.items()}
    return web.json({"alert_counts": counts})


if __name__ == "__main__":
    app.main()
