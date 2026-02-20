"""
Solution: Exercise 2.2 -- Top-N Leaderboard with Windowed Aggregation.

Tracks player scores in a 10-minute tumbling window and maintains an
all-time leaderboard. Exposes the top 5 players via an HTTP endpoint.

Usage:
    faust -A solutions.exercise_02_2_leaderboard worker -l info --web-port 6066

    curl http://localhost:6066/leaderboard/

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class GameEvent(faust.Record):
    """A game score event.

    Attributes:
        player_id: Unique identifier for the player.
        game_id: Identifier for the game session.
        score: Points earned in this event.
        timestamp: When the score was recorded.
    """

    player_id: str
    game_id: str
    score: int
    timestamp: datetime


# ---------------------------------------------------------------------------
# App, Topics, Tables
# ---------------------------------------------------------------------------

app = faust.App(
    "leaderboard-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

game_topic = app.topic("game-events", value_type=GameEvent, partitions=4)

# Windowed table: scores in the current 10-minute window
player_scores_windowed = app.Table(
    "player-scores",
    default=int,
).tumbling(
    timedelta(minutes=10),
    expires=timedelta(hours=2),
)

# All-time scores (non-windowed)
all_time_scores = app.Table("all-time-scores", default=int)

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


@app.agent(game_topic)
async def track_scores(stream):
    """Track player scores in both windowed and all-time tables.

    For each game event:
    1. Add the score to the 10-minute windowed table.
    2. Add the score to the all-time table.
    3. Print the current windowed score for the player.
    """
    async for event in stream:
        player_scores_windowed[event.player_id] += event.score
        all_time_scores[event.player_id] += event.score

        current_window_score = player_scores_windowed[event.player_id].current()

        print(
            f"[SCORE] player={event.player_id} "
            f"+{event.score} pts | "
            f"window={current_window_score} | "
            f"all_time={all_time_scores[event.player_id]}"
        )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/leaderboard/")
async def leaderboard(web, request):
    """Return the top 5 players sorted by all-time score descending."""
    scores = [(player, score) for player, score in all_time_scores.items()]
    scores.sort(key=lambda x: x[1], reverse=True)
    top_5 = scores[:5]

    leaderboard_data = [
        {"rank": i + 1, "player_id": player, "all_time_score": score}
        for i, (player, score) in enumerate(top_5)
    ]

    return web.json(
        {
            "leaderboard": leaderboard_data,
            "total_players": len(scores),
            "queried_at": datetime.utcnow().isoformat(),
        }
    )


@app.page("/player/{player_id}/")
async def player_stats(web, request, player_id):
    """Return stats for a specific player."""
    all_time = all_time_scores.get(player_id, 0)
    try:
        current_window = player_scores_windowed[player_id].current()
    except Exception:
        current_window = 0

    return web.json(
        {
            "player_id": player_id,
            "all_time_score": all_time,
            "current_window_score": current_window,
        }
    )


if __name__ == "__main__":
    app.main()
