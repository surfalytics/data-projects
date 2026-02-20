"""
Basic Faust Application -- Message Transformation Pipeline.

This application demonstrates the fundamentals of Faust stream processing:
- Creating a Faust App with Kafka broker configuration
- Defining input and output topics with typed Record models
- Writing an Agent that reads, transforms, and forwards messages

The agent reads raw messages from an input topic, transforms them (uppercases
the content and counts words), and writes the result to an output topic.

Usage:
    # Start Kafka (docker-compose up -d), then run:
    faust -A src.app_basic worker -l info

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime

from .models import RawMessage, TransformedMessage

# ---------------------------------------------------------------------------
# Faust App
# ---------------------------------------------------------------------------

app = faust.App(
    "basic-transform-app",
    broker="kafka://localhost:9092",
    store="memory://",  # Use in-memory store for simplicity
    topic_partitions=4,
    value_serializer="json",
)

# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

raw_topic = app.topic(
    "raw-messages",
    value_type=RawMessage,
    partitions=4,
)

transformed_topic = app.topic(
    "transformed-messages",
    value_type=TransformedMessage,
    partitions=4,
)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@app.agent(raw_topic)
async def transform_messages(stream):
    """Read raw messages, transform them, and write to the output topic.

    Transformation steps:
    1. Convert content to uppercase.
    2. Count the number of words.
    3. Attach a processing timestamp.
    """
    async for message in stream:
        upper_content = message.content.upper()
        word_count = len(message.content.split())

        transformed = TransformedMessage(
            original_id=message.message_id,
            content=upper_content,
            word_count=word_count,
            processed_at=datetime.utcnow(),
        )

        await transformed_topic.send(value=transformed)

        print(
            f"[transform] {message.message_id}: "
            f"'{message.content[:40]}...' -> {word_count} words"
        )


@app.agent(transformed_topic)
async def log_transformed(stream):
    """Sink agent that logs transformed messages for verification."""
    async for message in stream:
        print(
            f"[sink] id={message.original_id} "
            f"words={message.word_count} "
            f"processed_at={message.processed_at}"
        )


# ---------------------------------------------------------------------------
# Web view -- simple health check
# ---------------------------------------------------------------------------


@app.page("/health/")
async def health(web, request):
    """Return a simple health-check response."""
    return web.json({"status": "ok", "app": "basic-transform-app"})


if __name__ == "__main__":
    app.main()
