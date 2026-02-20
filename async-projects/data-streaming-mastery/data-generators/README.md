# Data Generators for Data Streaming Mastery

Reusable data generators that feed realistic, continuous data into the infrastructure
used across every module of the course. Each generator is a standalone CLI tool
that can run independently or alongside the others.

| Generator | Sink | Default Topic / DB | Primary Modules |
|---|---|---|---|
| `ecommerce_simulator.py` | MySQL | `ecommerce` database | 05 (CDC/Debezium), 09 (Capstone) |
| `clickstream_generator.py` | Kafka | `clickstream` topic | 02 (Kafka Core), 06 (ksqlDB), 07 (Faust), 08 (Flink) |
| `iot_sensor_generator.py` | Kafka | `iot-sensors` topic | 02 (Kafka Core), 03 (Schema Registry), 08 (Flink) |

---

## Prerequisites

1. **Python 3.9+**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Docker services** (started from the project root):
   ```bash
   docker-compose up -d
   ```
   The compose file brings up Kafka, Zookeeper, Schema Registry, MySQL,
   and other services used by downstream modules.

---

## 1. E-Commerce Simulator (`ecommerce_simulator.py`)

Writes realistic e-commerce activity directly into MySQL using SQLAlchemy.
Simulates the full customer lifecycle:

```
register -> browse -> add to cart -> purchase -> order status transitions
```

Orders progress through: `pending -> confirmed -> shipped -> delivered`.
Roughly 5% of orders are cancelled and 3% are returned after delivery.

### Usage

```bash
# Default settings (2 events/sec, 5 minutes, localhost MySQL)
python ecommerce_simulator.py

# Customized
python ecommerce_simulator.py \
    --speed 5 \
    --duration 600 \
    --mysql-host localhost \
    --mysql-port 3306 \
    --mysql-user root \
    --mysql-password debezium \
    --mysql-database ecommerce
```

### CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--speed` | `2` | Target events per second |
| `--duration` | `300` | Simulation duration in seconds |
| `--mysql-host` | `localhost` | MySQL hostname |
| `--mysql-port` | `3306` | MySQL port |
| `--mysql-user` | `root` | MySQL user |
| `--mysql-password` | `debezium` | MySQL password |
| `--mysql-database` | `ecommerce` | MySQL database name |

### Example Output

```
2026-02-19 10:00:01 [INFO] ecommerce_simulator — Connected to MySQL at localhost:3306/ecommerce
2026-02-19 10:00:01 [INFO] ecommerce_simulator — Seeded 15 products
2026-02-19 10:00:01 [INFO] ecommerce_simulator — Starting e-commerce simulation: speed=2 evt/s, duration=300s
2026-02-19 10:00:02 [INFO] ecommerce_simulator — Registered customer id=1 name=John Smith
2026-02-19 10:00:02 [INFO] ecommerce_simulator — Customer 1 browsed 3 products: Wireless Bluetooth Headphones, Yoga Mat, USB-C Hub
2026-02-19 10:00:03 [INFO] ecommerce_simulator — Customer 1 added 2 item(s) to cart
2026-02-19 10:00:04 [INFO] ecommerce_simulator — Customer 1 placed order #1 — total=$114.98
2026-02-19 10:00:05 [INFO] ecommerce_simulator — Order #1 status: pending -> confirmed
2026-02-19 10:00:06 [INFO] ecommerce_simulator — Order #1 status: confirmed -> shipped
```

### Tables Created

- `customers` — id, name, email, address, created_at
- `products` — id, name, category, price, inventory_qty
- `orders` — id, customer_id, status, total, created_at, updated_at
- `order_items` — id, order_id, product_id, quantity, unit_price
- `cart_items` — id, customer_id, product_id, quantity, added_at

---

## 2. Clickstream Generator (`clickstream_generator.py`)

Produces session-based web analytics events to a Kafka topic. Each session
simulates a visitor navigating an e-commerce website following realistic
transition probabilities:

```
home -> category -> product -> add_to_cart -> cart -> checkout
```

Not every session reaches checkout — the funnel narrows naturally.

### Usage

```bash
# Default settings (5 events/sec, 5 minutes, localhost Kafka)
python clickstream_generator.py

# Customized
python clickstream_generator.py \
    --speed 10 \
    --duration 600 \
    --kafka-bootstrap-servers localhost:9092 \
    --topic clickstream
```

### CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--speed` | `5` | Target events per second |
| `--duration` | `300` | Generation duration in seconds |
| `--kafka-bootstrap-servers` | `localhost:9092` | Kafka broker address |
| `--topic` | `clickstream` | Kafka topic to produce to |

### Example Output

```
2026-02-19 10:00:01 [INFO] clickstream_generator — Kafka producer created (bootstrap: localhost:9092)
2026-02-19 10:00:01 [INFO] clickstream_generator — Starting clickstream generation: speed=5 evt/s, duration=300s, topic=clickstream
2026-02-19 10:05:01 [INFO] clickstream_generator — Clickstream generation complete: 142 sessions, 1487 events produced.
```

### Event Schema

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user_42567",
  "event_type": "page_view",
  "page_url": "https://shop.example.com/c/electronics",
  "referrer": "https://www.google.com/",
  "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
  "ip_address": "203.0.113.42",
  "geo": {"city": "San Francisco", "country": "US"},
  "device_type": "desktop",
  "timestamp": "2026-02-19T10:00:02.123456+00:00"
}
```

---

## 3. IoT Sensor Generator (`iot_sensor_generator.py`)

Simulates a fleet of IoT devices sending periodic telemetry to a Kafka topic.
Readings evolve realistically over time with gradual drift and occasional
anomalies.

Device types: `thermostat` (Celsius), `humidity` (%), `pressure` (hPa).

Anomaly modes:
- **Spike** — sudden jump far outside normal range
- **Dropout** — null reading (heartbeat without data)
- **Out-of-range** — physically impossible value (e.g., -999)

### Usage

```bash
# Default settings (20 devices, 10 events/sec, 5 minutes)
python iot_sensor_generator.py

# Customized
python iot_sensor_generator.py \
    --speed 20 \
    --duration 600 \
    --devices 50 \
    --anomaly-rate 0.05 \
    --kafka-bootstrap-servers localhost:9092 \
    --topic iot-sensors
```

### CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--speed` | `10` | Target events per second (across all devices) |
| `--duration` | `300` | Generation duration in seconds |
| `--devices` | `20` | Number of simulated IoT devices |
| `--anomaly-rate` | `0.02` | Fraction of anomalous readings (0.02 = 2%) |
| `--kafka-bootstrap-servers` | `localhost:9092` | Kafka broker address |
| `--topic` | `iot-sensors` | Kafka topic to produce to |

### Example Output

```
2026-02-19 10:00:01 [INFO] iot_sensor_generator — Created fleet of 20 devices: device-0001(thermostat), device-0002(humidity), ...
2026-02-19 10:00:01 [INFO] iot_sensor_generator — Starting IoT generation: 20 devices, speed=10.0 evt/s, duration=300s, anomaly_rate=0.02, topic=iot-sensors
2026-02-19 10:00:31 [INFO] iot_sensor_generator — Progress: 200 events produced (4 anomalies)
2026-02-19 10:05:01 [INFO] iot_sensor_generator — IoT generation complete: 3000 events produced (61 anomalies, 2.0%).
```

### Event Schema

```json
{
  "device_id": "device-0007",
  "device_type": "thermostat",
  "reading": 23.47,
  "unit": "celsius",
  "battery_level": 87.3,
  "anomaly": null,
  "location": {"zone": "server-room", "lat": 37.7849, "lng": -122.4295},
  "firmware_version": "1.2.3",
  "timestamp": "2026-02-19T10:00:05.654321+00:00"
}
```

---

## Using Generators with Course Modules

### Module 02 — Kafka Core
Run the clickstream or IoT generator, then consume with `kafka-console-consumer`:
```bash
python clickstream_generator.py --speed 2 --duration 120
```

### Module 03 — Schema Registry
Use the IoT generator output and register an Avro/JSON schema for the sensor events.

### Module 05 — CDC with Debezium
Start the e-commerce simulator, then configure a Debezium MySQL connector to
capture changes from the `ecommerce` database.

### Module 06 — ksqlDB
Create streaming queries over the `clickstream` topic produced by the clickstream
generator.

### Module 07 — Faust Streaming
Build Faust agents that consume and process `clickstream` or `iot-sensors` events.

### Module 08 — Flink
Create Flink SQL jobs that join clickstream data with IoT sensor data for
real-time analytics dashboards.

### Module 09 — Capstone
All three generators run simultaneously, feeding the full end-to-end pipeline.

---

## Stopping Generators

All generators handle `Ctrl+C` (SIGINT) gracefully. They will:
1. Stop producing new events
2. Flush any buffered Kafka messages
3. Close database connections
4. Print a summary of events produced
