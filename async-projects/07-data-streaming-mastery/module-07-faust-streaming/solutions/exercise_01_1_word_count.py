"""
Solution: Exercise 1.1 -- Word Count Agent.

A Faust agent that reads text messages, splits them into words,
and maintains a running word count in a Faust Table. Includes a
web view to query the count for any word.

Usage:
    faust -A solutions.exercise_01_1_word_count worker -l info --web-port 6066

    # Query a word count:
    curl http://localhost:6066/words/hello/

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class TextMessage(faust.Record):
    """A text message to be word-counted.

    Attributes:
        message_id: Unique identifier for the message.
        text: The text content to split into words.
        timestamp: When the message was created.
    """

    message_id: str
    text: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# App, Topics, Tables
# ---------------------------------------------------------------------------

app = faust.App(
    "word-count-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

text_topic = app.topic("text-messages", value_type=TextMessage, partitions=4)

word_counts = app.Table("word-counts", default=int)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@app.agent(text_topic)
async def count_words(stream):
    """Read text messages, split into words, and count occurrences.

    Each word is lowercased before counting. The running count for every
    word seen in the current message is printed to stdout.
    """
    async for message in stream:
        words = message.text.lower().split()
        for word in words:
            # Strip punctuation from edges
            cleaned = word.strip(".,!?;:\"'()[]{}/-")
            if cleaned:
                word_counts[cleaned] += 1
                print(f"[word-count] '{cleaned}' -> {word_counts[cleaned]}")


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/words/{word}/")
async def get_word_count(web, request, word):
    """Return the count for a specific word."""
    count = word_counts.get(word.lower(), 0)
    return web.json({"word": word.lower(), "count": count})


@app.page("/words/")
async def get_all_words(web, request):
    """Return all word counts."""
    all_words = {k: v for k, v in word_counts.items()}
    return web.json({"total_unique_words": len(all_words), "counts": all_words})


if __name__ == "__main__":
    app.main()
