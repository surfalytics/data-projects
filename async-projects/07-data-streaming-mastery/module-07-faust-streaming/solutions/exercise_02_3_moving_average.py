"""
Solution: Exercise 2.3 -- Moving Average Calculator.

Computes a moving average of stock prices using hopping windows.
A 5-minute window with a 1-minute hop means each tick contributes
to 5 overlapping windows, giving a smooth moving average.

Usage:
    faust -A solutions.exercise_02_3_moving_average worker -l info --web-port 6066

    curl http://localhost:6066/stocks/AAPL/

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class StockTick(faust.Record):
    """A stock price tick event.

    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL').
        price: Current price in USD.
        volume: Number of shares traded.
        timestamp: When the tick occurred.
    """

    symbol: str
    price: float
    volume: int
    timestamp: datetime


# ---------------------------------------------------------------------------
# App, Topics, Tables
# ---------------------------------------------------------------------------

app = faust.App(
    "moving-average-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

ticks_topic = app.topic("stock-ticks", value_type=StockTick, partitions=4)

# Hopping window: 5-minute size, 1-minute step
# price_sum accumulates the total price in each window
price_sum = app.Table(
    "price-sum",
    default=float,
).hopping(
    timedelta(minutes=5),
    timedelta(minutes=1),
    expires=timedelta(hours=1),
)

# tick_count tracks how many ticks in each window
tick_count = app.Table(
    "tick-count",
    default=int,
).hopping(
    timedelta(minutes=5),
    timedelta(minutes=1),
    expires=timedelta(hours=1),
)

# Non-windowed table for latest price (for web view)
latest_price = app.Table("latest-price", default=float)

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


@app.agent(ticks_topic)
async def compute_moving_average(stream):
    """Compute a moving average of stock prices using hopping windows.

    For each tick:
    1. Group by symbol.
    2. Add the price to price_sum and increment tick_count.
    3. Compute moving_average = price_sum / tick_count for the current window.
    4. Print the symbol, current price, and moving average.
    """
    async for tick in stream.group_by(StockTick.symbol):
        price_sum[tick.symbol] += tick.price
        tick_count[tick.symbol] += 1
        latest_price[tick.symbol] = tick.price

        current_sum = price_sum[tick.symbol].current()
        current_count = tick_count[tick.symbol].current()

        if current_count > 0:
            moving_avg = current_sum / current_count
        else:
            moving_avg = tick.price

        print(
            f"[STOCK] {tick.symbol}: "
            f"price=${tick.price:,.2f} | "
            f"5min_avg=${moving_avg:,.2f} | "
            f"ticks_in_window={current_count} | "
            f"volume={tick.volume}"
        )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/stocks/{symbol}/")
async def stock_moving_average(web, request, symbol):
    """Return the latest moving average for a given stock symbol."""
    symbol = symbol.upper()

    try:
        current_sum = price_sum[symbol].current()
        current_count = tick_count[symbol].current()
        if current_count > 0:
            moving_avg = current_sum / current_count
        else:
            moving_avg = 0.0
    except Exception:
        current_sum = 0.0
        current_count = 0
        moving_avg = 0.0

    return web.json(
        {
            "symbol": symbol,
            "latest_price": latest_price.get(symbol, 0.0),
            "moving_average_5min": round(moving_avg, 2),
            "ticks_in_window": current_count,
            "window_size_minutes": 5,
            "hop_size_minutes": 1,
            "queried_at": datetime.utcnow().isoformat(),
        }
    )


@app.page("/stocks/")
async def all_stocks(web, request):
    """Return latest prices for all tracked symbols."""
    stocks = {k: v for k, v in latest_price.items()}
    return web.json({"tracked_symbols": len(stocks), "latest_prices": stocks})


if __name__ == "__main__":
    app.main()
