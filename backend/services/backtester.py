import pandas as pd
import numpy as np
import yfinance as yf
import logging
from typing import Optional

from services.technical_analysis import compute_indicator_series
from services.data_sources import fetch_history_df_with_fallback, _is_us_stock_symbol

logger = logging.getLogger(__name__)

INITIAL_CAPITAL = 100_000


def _calculate_metrics(equity_curve: pd.Series, trades: list[dict]) -> dict:
    """Calculate performance metrics from equity curve and trades."""
    if len(equity_curve) < 2:
        return _empty_metrics()

    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
    days = (equity_curve.index[-1] - equity_curve.index[0]).days
    annual_return = ((1 + total_return / 100) ** (365.0 / max(days, 1)) - 1) * 100

    daily_returns = equity_curve.pct_change().dropna()
    sharpe_ratio = 0.0
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

    rolling_max = equity_curve.expanding().max()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100

    winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
    win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0

    gross_profit = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0

    return {
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown": round(max_drawdown, 2),
        "win_rate": round(win_rate, 2),
        "num_trades": len(trades),
        "profit_factor": round(min(profit_factor, 999.99), 2),
    }


def _empty_metrics() -> dict:
    return {
        "total_return": 0, "annual_return": 0, "sharpe_ratio": 0,
        "max_drawdown": 0, "win_rate": 0, "num_trades": 0, "profit_factor": 0,
    }


def _build_equity_curve_output(equity_curve: pd.Series) -> list[dict]:
    return [
        {"date": date.strftime("%Y-%m-%d"), "value": round(val, 2)}
        for date, val in equity_curve.items()
    ]


def run_backtest(ticker: str, strategy: str, params: dict, period: str = "2y") -> dict:
    """Run a backtest for the given ticker and strategy. Uses yfinance with akshare fallback for US stocks."""
    try:
        period = (period or "2y").lower()
        df = fetch_history_df_with_fallback(ticker, period)
        if df is None or df.empty or len(df) < 50:
            if period != "max" and _is_us_stock_symbol(ticker):
                df = fetch_history_df_with_fallback(ticker, "max")
            if df is None or df.empty or len(df) < 50:
                return {"error": f"Insufficient data for {ticker} (got {len(df) if df is not None else 0} rows, need 50+). Try a different ticker or check if it's tradeable."}

        df = compute_indicator_series(df)

        if strategy == "ma_crossover":
            return _ma_crossover(df, params)
        elif strategy == "momentum":
            return _momentum(df, params)
        elif strategy == "mean_reversion":
            return _mean_reversion(df, params)
        else:
            return {"error": f"Unknown strategy: {strategy}"}

    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return {"error": str(e)}


def _ma_crossover(df: pd.DataFrame, params: dict) -> dict:
    """Moving average crossover strategy."""
    fast = params.get("fast_period", 20)
    slow = params.get("slow_period", 50)

    df = df.copy()
    df["fast_ma"] = df["Close"].rolling(fast).mean()
    df["slow_ma"] = df["Close"].rolling(slow).mean()
    df.dropna(inplace=True)

    if len(df) < 2:
        return {"metrics": _empty_metrics(), "equity_curve": [], "trades": []}

    position = 0
    cash = INITIAL_CAPITAL
    shares = 0
    trades = []
    equity = []

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        date = df.index[i]

        if prev["fast_ma"] <= prev["slow_ma"] and row["fast_ma"] > row["slow_ma"] and position == 0:
            shares = cash / row["Close"]
            cash = 0
            position = 1
            trades.append({
                "date": date.strftime("%Y-%m-%d"),
                "type": "BUY",
                "price": round(row["Close"], 2),
                "shares": round(shares, 4),
            })

        elif prev["fast_ma"] >= prev["slow_ma"] and row["fast_ma"] < row["slow_ma"] and position == 1:
            cash = shares * row["Close"]
            pnl = cash - INITIAL_CAPITAL if not trades else cash - (trades[-1]["price"] * shares)
            position = 0
            trades.append({
                "date": date.strftime("%Y-%m-%d"),
                "type": "SELL",
                "price": round(row["Close"], 2),
                "shares": round(shares, 4),
                "pnl": round(pnl, 2),
            })
            shares = 0

        portfolio_value = cash + shares * row["Close"]
        equity.append((date, portfolio_value))

    if position == 1:
        cash = shares * df.iloc[-1]["Close"]
        pnl = cash - (trades[-1]["price"] * shares) if trades else 0
        trades.append({
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "type": "SELL",
            "price": round(df.iloc[-1]["Close"], 2),
            "shares": round(shares, 4),
            "pnl": round(pnl, 2),
        })

    equity_series = pd.Series(
        [v for _, v in equity],
        index=pd.DatetimeIndex([d for d, _ in equity])
    )

    return {
        "metrics": _calculate_metrics(equity_series, [t for t in trades if t["type"] == "SELL"]),
        "equity_curve": _build_equity_curve_output(equity_series),
        "trades": trades,
    }


def _momentum(df: pd.DataFrame, params: dict) -> dict:
    """RSI momentum strategy: buy when RSI crosses above oversold, sell when overbought."""
    rsi_buy = params.get("rsi_buy", 30)
    rsi_sell = params.get("rsi_sell", 70)

    if "RSI" not in df.columns:
        return {"metrics": _empty_metrics(), "equity_curve": [], "trades": []}

    df = df.dropna(subset=["RSI"]).copy()
    if len(df) < 2:
        return {"metrics": _empty_metrics(), "equity_curve": [], "trades": []}

    position = 0
    cash = INITIAL_CAPITAL
    shares = 0
    trades = []
    equity = []

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        date = df.index[i]

        if prev["RSI"] <= rsi_buy and row["RSI"] > rsi_buy and position == 0:
            shares = cash / row["Close"]
            cash = 0
            position = 1
            trades.append({
                "date": date.strftime("%Y-%m-%d"),
                "type": "BUY",
                "price": round(row["Close"], 2),
                "shares": round(shares, 4),
            })

        elif prev["RSI"] < rsi_sell and row["RSI"] >= rsi_sell and position == 1:
            cash = shares * row["Close"]
            pnl = cash - (trades[-1]["price"] * shares) if trades else 0
            position = 0
            trades.append({
                "date": date.strftime("%Y-%m-%d"),
                "type": "SELL",
                "price": round(row["Close"], 2),
                "shares": round(shares, 4),
                "pnl": round(pnl, 2),
            })
            shares = 0

        portfolio_value = cash + shares * row["Close"]
        equity.append((date, portfolio_value))

    if position == 1:
        cash = shares * df.iloc[-1]["Close"]
        pnl = cash - (trades[-1]["price"] * shares) if trades else 0
        trades.append({
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "type": "SELL",
            "price": round(df.iloc[-1]["Close"], 2),
            "shares": round(shares, 4),
            "pnl": round(pnl, 2),
        })

    equity_series = pd.Series(
        [v for _, v in equity],
        index=pd.DatetimeIndex([d for d, _ in equity])
    )

    return {
        "metrics": _calculate_metrics(equity_series, [t for t in trades if t["type"] == "SELL"]),
        "equity_curve": _build_equity_curve_output(equity_series),
        "trades": trades,
    }


def _mean_reversion(df: pd.DataFrame, params: dict) -> dict:
    """Bollinger Band mean reversion: buy at lower band, sell at upper band."""
    if "BB_Lower" not in df.columns or "BB_Upper" not in df.columns:
        return {"metrics": _empty_metrics(), "equity_curve": [], "trades": []}

    df = df.dropna(subset=["BB_Lower", "BB_Upper"]).copy()
    if len(df) < 2:
        return {"metrics": _empty_metrics(), "equity_curve": [], "trades": []}

    position = 0
    cash = INITIAL_CAPITAL
    shares = 0
    trades = []
    equity = []

    for i in range(len(df)):
        row = df.iloc[i]
        date = df.index[i]

        if row["Close"] <= row["BB_Lower"] and position == 0:
            shares = cash / row["Close"]
            cash = 0
            position = 1
            trades.append({
                "date": date.strftime("%Y-%m-%d"),
                "type": "BUY",
                "price": round(row["Close"], 2),
                "shares": round(shares, 4),
            })

        elif row["Close"] >= row["BB_Upper"] and position == 1:
            cash = shares * row["Close"]
            pnl = cash - (trades[-1]["price"] * shares) if trades else 0
            position = 0
            trades.append({
                "date": date.strftime("%Y-%m-%d"),
                "type": "SELL",
                "price": round(row["Close"], 2),
                "shares": round(shares, 4),
                "pnl": round(pnl, 2),
            })
            shares = 0

        portfolio_value = cash + shares * row["Close"]
        equity.append((date, portfolio_value))

    if position == 1:
        cash = shares * df.iloc[-1]["Close"]
        pnl = cash - (trades[-1]["price"] * shares) if trades else 0
        trades.append({
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "type": "SELL",
            "price": round(df.iloc[-1]["Close"], 2),
            "shares": round(shares, 4),
            "pnl": round(pnl, 2),
        })

    equity_series = pd.Series(
        [v for _, v in equity],
        index=pd.DatetimeIndex([d for d, _ in equity])
    )

    return {
        "metrics": _calculate_metrics(equity_series, [t for t in trades if t["type"] == "SELL"]),
        "equity_curve": _build_equity_curve_output(equity_series),
        "trades": trades,
    }
