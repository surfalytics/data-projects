"""
Solution: Exercise 2.1 -- Session Tracker.

Tracks active user sessions using a Faust Table. Detects when a user has
been inactive for more than 5 minutes and marks their session as expired.

Usage:
    faust -A solutions.exercise_02_1_session_tracker worker -l info --web-port 6066

    curl http://localhost:6066/sessions/
    curl http://localhost:6066/sessions/user-0001/

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class UserActivity(faust.Record):
    """A user activity event.

    Attributes:
        user_id: Unique identifier for the user.
        action: The action performed (e.g., 'click', 'view', 'purchase').
        page: The page or screen where the action occurred.
        timestamp: When the action happened.
    """

    user_id: str
    action: str
    page: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# App, Topics, Tables
# ---------------------------------------------------------------------------

app = faust.App(
    "session-tracker-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

activity_topic = app.topic("user-activities", value_type=UserActivity, partitions=4)

# Session table: stores dicts with session state per user
user_sessions = app.Table("user-sessions", default=dict)

SESSION_TIMEOUT = timedelta(minutes=5)

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


@app.agent(activity_topic)
async def track_sessions(stream):
    """Track user sessions and detect inactivity timeouts.

    For each activity event:
    - If the user has no session or their session has expired (>5 min since
      last_seen), start a new session.
    - Otherwise, update the existing session with the new activity.
    """
    async for activity in stream:
        user_id = activity.user_id
        session = user_sessions.get(user_id, {})
        now = datetime.utcnow()

        # Check for session expiration
        if session and session.get("last_seen"):
            try:
                last_seen = datetime.fromisoformat(session["last_seen"])
                if now - last_seen > SESSION_TIMEOUT:
                    print(
                        f"[SESSION EXPIRED] user={user_id} "
                        f"inactive for {(now - last_seen).total_seconds():.0f}s "
                        f"(actions in session: {session.get('action_count', 0)})"
                    )
                    # Reset the session
                    session = {}
            except (ValueError, TypeError):
                session = {}

        # Update or create session
        if not session:
            # New session
            session = {
                "last_action": activity.action,
                "last_page": activity.page,
                "action_count": 1,
                "last_seen": now.isoformat(),
                "session_start": now.isoformat(),
            }
            print(f"[NEW SESSION] user={user_id} started on page={activity.page}")
        else:
            # Update existing session
            session["last_action"] = activity.action
            session["last_page"] = activity.page
            session["action_count"] = session.get("action_count", 0) + 1
            session["last_seen"] = now.isoformat()
            print(
                f"[SESSION UPDATE] user={user_id} "
                f"action={activity.action} page={activity.page} "
                f"actions={session['action_count']}"
            )

        user_sessions[user_id] = session


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/sessions/")
async def all_sessions(web, request):
    """Return all active user sessions."""
    sessions = {k: v for k, v in user_sessions.items()}
    return web.json({"active_sessions": len(sessions), "sessions": sessions})


@app.page("/sessions/{user_id}/")
async def user_session(web, request, user_id):
    """Return the session for a specific user."""
    session = user_sessions.get(user_id, {})
    if session:
        return web.json({"user_id": user_id, "session": session})
    else:
        return web.json({"user_id": user_id, "session": None, "message": "No active session"})


if __name__ == "__main__":
    app.main()
