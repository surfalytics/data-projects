# Exercise 02: Stateful Processing with Tables and Windows

## Prerequisites

- Kafka running locally (`docker-compose up -d` from the module root)
- `faust-streaming` installed (`pip install -r requirements.txt`)
- Completed Exercise 01 or familiarity with Faust agents

---

## Exercise 2.1: Session Tracker

**Objective:** Track active user sessions using a Faust Table. Detect when a user has been inactive for more than 5 minutes and mark their session as expired.

**Requirements:**

1. Create a Faust app named `"session-tracker-app"`.
2. Define a `UserActivity` Record with: `user_id` (str), `action` (str), `page` (str), `timestamp` (datetime).
3. Create a table `"user-sessions"` that stores session data as a dict (with keys: `last_action`, `last_page`, `action_count`, `last_seen`).
4. Write an agent that:
   - On each activity event, updates the user's session in the table.
   - Checks if the time since `last_seen` exceeds 5 minutes. If so, prints a "session expired" message and resets the session.
   - Otherwise, increments `action_count` and updates `last_seen`.
5. Add a web view at `/sessions/` that returns all active sessions.
6. Add a web view at `/sessions/{user_id}/` that returns the session for a specific user.

**Hints:**
- Store `last_seen` as an ISO timestamp string, then parse it to compare.
- Use `datetime.fromisoformat()` to parse stored timestamps.

**File:** Save your solution as `solutions/exercise_02_1_session_tracker.py`

---

## Exercise 2.2: Top-N Leaderboard with Windowed Aggregation

**Objective:** Build a real-time leaderboard that tracks the top 5 scorers in a 10-minute tumbling window.

**Requirements:**

1. Create a Faust app named `"leaderboard-app"`.
2. Define a `GameEvent` Record with: `player_id` (str), `game_id` (str), `score` (int), `timestamp` (datetime).
3. Create a tumbling windowed table `"player-scores"` with a 10-minute window.
4. Create a non-windowed table `"all-time-scores"` (default=int) for all-time tracking.
5. Write an agent that:
   - Adds each event's score to both the windowed and all-time tables.
   - After each update, prints the current windowed score for that player.
6. Add a web view at `/leaderboard/` that:
   - Reads all entries from `all-time-scores`.
   - Returns the top 5 players sorted by score descending.

**Hints:**
- Use `.tumbling(timedelta(minutes=10), expires=timedelta(hours=2))`.
- For the leaderboard, iterate over `all_time_scores.items()` and sort.

**File:** Save your solution as `solutions/exercise_02_2_leaderboard.py`

---

## Exercise 2.3: Moving Average Calculator

**Objective:** Compute a moving average of stock prices using a hopping window.

**Requirements:**

1. Create a Faust app named `"moving-average-app"`.
2. Define a `StockTick` Record with: `symbol` (str), `price` (float), `volume` (int), `timestamp` (datetime).
3. Create two tables:
   - `"price-sum"`: hopping window (5-minute size, 1-minute step), default=float -- stores cumulative price.
   - `"tick-count"`: hopping window (5-minute size, 1-minute step), default=int -- stores number of ticks.
4. Write an agent that:
   - Groups by `symbol`.
   - For each tick, adds the price to `price-sum` and increments `tick-count`.
   - Computes the moving average as `price_sum / tick_count` for the current window.
   - Prints the symbol, current price, and moving average.
5. Add a web view at `/stocks/{symbol}/` that returns the latest moving average for a given symbol.

**Hints:**
- Use `.hopping(timedelta(minutes=5), timedelta(minutes=1), expires=timedelta(hours=1))`.
- Access current window values with `.current()`.
- Handle division by zero when tick_count is 0.

**File:** Save your solution as `solutions/exercise_02_3_moving_average.py`
