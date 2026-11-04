"""
Solution: Exercise 1.3 -- Multi-Step Pipeline.

A three-stage Faust processing pipeline:
  Stage 1 (Validation): Check payload is non-empty and source is valid.
  Stage 2 (Enrichment): Compute word_count and char_count.
  Stage 3 (Sink): Print a formatted summary.

Usage:
    faust -A solutions.exercise_01_3_pipeline worker -l info

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

VALID_SOURCES = {"web", "mobile", "api"}


class RawEvent(faust.Record):
    """Raw input event before validation.

    Attributes:
        event_id: Unique event identifier.
        payload: The event payload text.
        source: The originating system.
    """

    event_id: str
    payload: str
    source: str


class ValidatedEvent(faust.Record):
    """An event that has passed validation.

    Attributes:
        event_id: Unique event identifier.
        payload: The validated payload text.
        is_valid: Whether the event passed validation (always True here).
    """

    event_id: str
    payload: str
    is_valid: bool


class EnrichedEvent(faust.Record):
    """A validated event enriched with computed metadata.

    Attributes:
        event_id: Unique event identifier.
        payload: The event payload text.
        word_count: Number of words in the payload.
        char_count: Number of characters in the payload.
        source: The originating system.
    """

    event_id: str
    payload: str
    word_count: int
    char_count: int
    source: str


# ---------------------------------------------------------------------------
# App, Topics
# ---------------------------------------------------------------------------

app = faust.App(
    "pipeline-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

raw_topic = app.topic("raw-events", value_type=RawEvent, partitions=4)
validated_topic = app.topic("validated-events", value_type=ValidatedEvent, partitions=4)
enriched_topic = app.topic("enriched-events", value_type=EnrichedEvent, partitions=4)

# Counters for monitoring
pipeline_stats = app.Table("pipeline-stats", default=int)

# ---------------------------------------------------------------------------
# Stage 1: Validation Agent
# ---------------------------------------------------------------------------


@app.agent(raw_topic)
async def validate_events(stream):
    """Validate raw events and forward valid ones downstream.

    Validation rules:
    - payload must not be empty
    - source must be one of: web, mobile, api
    """
    async for event in stream:
        pipeline_stats["received"] += 1

        if not event.payload or not event.payload.strip():
            pipeline_stats["rejected_empty_payload"] += 1
            print(f"[VALIDATE] REJECTED {event.event_id}: empty payload")
            continue

        if event.source not in VALID_SOURCES:
            pipeline_stats["rejected_bad_source"] += 1
            print(
                f"[VALIDATE] REJECTED {event.event_id}: "
                f"invalid source '{event.source}'"
            )
            continue

        validated = ValidatedEvent(
            event_id=event.event_id,
            payload=event.payload,
            is_valid=True,
        )
        await validated_topic.send(value=validated)
        pipeline_stats["validated"] += 1
        print(f"[VALIDATE] PASSED {event.event_id}")


# ---------------------------------------------------------------------------
# Stage 2: Enrichment Agent
# ---------------------------------------------------------------------------


@app.agent(validated_topic)
async def enrich_events(stream):
    """Enrich validated events with computed metadata."""
    async for event in stream:
        word_count = len(event.payload.split())
        char_count = len(event.payload)

        enriched = EnrichedEvent(
            event_id=event.event_id,
            payload=event.payload,
            word_count=word_count,
            char_count=char_count,
            source="validated",  # Mark as processed
        )
        await enriched_topic.send(value=enriched)
        pipeline_stats["enriched"] += 1
        print(
            f"[ENRICH] {event.event_id}: "
            f"words={word_count}, chars={char_count}"
        )


# ---------------------------------------------------------------------------
# Stage 3: Sink Agent
# ---------------------------------------------------------------------------


@app.agent(enriched_topic)
async def sink_events(stream):
    """Final stage: log enriched events in a formatted summary."""
    async for event in stream:
        pipeline_stats["completed"] += 1
        print(
            f"[SINK] === Event Summary ===\n"
            f"  ID:         {event.event_id}\n"
            f"  Payload:    {event.payload[:80]}{'...' if len(event.payload) > 80 else ''}\n"
            f"  Words:      {event.word_count}\n"
            f"  Characters: {event.char_count}\n"
            f"  Source:     {event.source}\n"
            f"  Pipeline total completed: {pipeline_stats['completed']}"
        )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/pipeline/stats/")
async def pipeline_stats_view(web, request):
    """Return pipeline processing statistics."""
    stats = {k: v for k, v in pipeline_stats.items()}
    return web.json({"pipeline_stats": stats})


if __name__ == "__main__":
    app.main()
