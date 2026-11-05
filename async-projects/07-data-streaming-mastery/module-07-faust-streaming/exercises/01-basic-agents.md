# Exercise 01: Basic Faust Agents

## Prerequisites

- Kafka running locally (`docker-compose up -d` from the module root)
- `faust-streaming` installed (`pip install -r requirements.txt`)
- Familiarity with Python `async/await`

---

## Exercise 1.1: Word Count Agent

**Objective:** Build a Faust agent that reads text messages from a topic, splits them into individual words, and maintains a running word count.

**Requirements:**

1. Create a Faust app named `"word-count-app"`.
2. Define a `TextMessage` Record with fields: `message_id` (str), `text` (str), `timestamp` (datetime).
3. Create an input topic `"text-messages"` with `value_type=TextMessage`.
4. Create a Faust Table called `"word-counts"` with `default=int`.
5. Write an agent that:
   - Reads from the `text-messages` topic.
   - Splits each message's `text` field into lowercase words.
   - Increments the count for each word in the table.
   - Prints the updated count for each word.
6. Add a web view at `/words/{word}/` that returns the count for a given word.

**Hints:**
- Use `message.text.lower().split()` to tokenize.
- Access table values with `word_counts[word]`.

**File:** Save your solution as `solutions/exercise_01_1_word_count.py`

---

## Exercise 1.2: Message Filter Agent

**Objective:** Build a Faust agent that filters a stream of events based on a condition and routes them to different output topics.

**Requirements:**

1. Create a Faust app named `"message-filter-app"`.
2. Define a `SensorReading` Record with fields: `sensor_id` (str), `temperature` (float), `humidity` (float), `timestamp` (datetime).
3. Create an input topic `"sensor-readings"`.
4. Create two output topics:
   - `"high-temp-alerts"` for readings where temperature > 35.0
   - `"normal-readings"` for all other readings
5. Write an agent that reads sensor events and routes them to the correct output topic.
6. Write a second agent that counts how many alerts have been produced and prints the running total.

**Hints:**
- Use `await output_topic.send(value=reading)` to route messages.
- Use a simple table or variable to track the alert count.

**File:** Save your solution as `solutions/exercise_01_2_message_filter.py`

---

## Exercise 1.3: Multi-Step Pipeline

**Objective:** Build a three-stage processing pipeline where each stage is a separate agent.

**Requirements:**

1. Create a Faust app named `"pipeline-app"`.
2. Define these Records:
   - `RawEvent`: `event_id` (str), `payload` (str), `source` (str)
   - `ValidatedEvent`: `event_id` (str), `payload` (str), `is_valid` (bool)
   - `EnrichedEvent`: `event_id` (str), `payload` (str), `word_count` (int), `char_count` (int), `source` (str)
3. Create three topics: `"raw-events"`, `"validated-events"`, `"enriched-events"`.
4. **Stage 1 -- Validation Agent:** Read from `raw-events`, check that `payload` is not empty and `source` is in `["web", "mobile", "api"]`. Send valid events to `validated-events`.
5. **Stage 2 -- Enrichment Agent:** Read from `validated-events`, compute `word_count` and `char_count` from the payload, send enriched events to `enriched-events`.
6. **Stage 3 -- Sink Agent:** Read from `enriched-events` and print a formatted summary of each event.

**Hints:**
- Each agent subscribes to a different topic.
- This models a real-world ETL pipeline: validate -> enrich -> load.

**File:** Save your solution as `solutions/exercise_01_3_pipeline.py`
