"""Backtesting engine: run strategies on OHLCV and compute metrics."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    side: str  # "long" | "short"
    pnl: float
    pnl_pct: float
    hold_bars: int


@dataclass
class BacktestResult:
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_equity: float
    total_return_pct: float
    sharpe_ratio: Optional[float]
    max_drawdown_pct: float
    win_rate_pct: float
    num_trades: int
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]


def _ensure_dataframe(ohlcv: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(ohlcv)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df


def _compute_equity_curve(equity_series: pd.Series) -> List[Dict[str, Any]]:
    return [{"date": str(d.date()), "equity": float(v)} for d, v in equity_series.items()]


def _compute_sharpe(returns: pd.Series, risk_free: float = 0.0, periods_per_year: float = 252) -> Optional[float]:
    if returns.empty or returns.std() == 0:
        return None
    excess = returns - (risk_free / periods_per_year)
    return float(excess.mean() / excess.std() * (periods_per_year ** 0.5))


def _compute_max_drawdown(equity: pd.Series) -> float:
    if equity.empty or len(equity) < 2:
        return 0.0
    cummax = equity.cummax()
    dd = (equity - cummax) / cummax * 100
    return float(dd.min())


# --- Strategy: Moving Average Crossover ---

def run_ma_crossover(
    ohlcv: List[Dict[str, Any]],
    symbol: str,
    fast_period: int = 10,
    slow_period: int = 30,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Long when fast MA crosses above slow MA; exit when crosses below."""
    df = _ensure_dataframe(ohlcv)
    if df.empty or len(df) < slow_period:
        return _empty_result(symbol, ohlcv, initial_capital)

    df["fast_ma"] = df["close"].rolling(fast_period).mean()
    df["slow_ma"] = df["close"].rolling(slow_period).mean()
    df["signal"] = 0
    df.loc[df["fast_ma"] > df["slow_ma"], "signal"] = 1
    df["position"] = df["signal"].diff().fillna(0)
    # position: 1 = enter long, -1 = exit
    entries = df[df["position"] == 1].index.tolist()
    exits = df[df["position"] == -1].index.tolist()

    trades: List[Trade] = []
    i_entry = 0
    for ex in exits:
        while i_entry < len(entries) and entries[i_entry] >= ex:
            i_entry += 1
        if i_entry == 0:
            continue
        entry_time = entries[i_entry - 1]
        entry_price = float(df.loc[entry_time, "close"])
        exit_price = float(df.loc[ex, "close"])
        hold_bars = (df.index.get_loc(ex) - df.index.get_loc(entry_time))
        pnl = exit_price - entry_price
        pnl_pct = (exit_price / entry_price - 1) * 100
        trades.append(Trade(
            entry_date=str(entry_time.date()),
            exit_date=str(ex.date()),
            entry_price=entry_price,
            exit_price=exit_price,
            side="long",
            pnl=pnl,
            pnl_pct=pnl_pct,
            hold_bars=hold_bars,
        ))

    return _build_result(df, trades, symbol, initial_capital, ohlcv)


# --- Strategy: Momentum (e.g. buy when price > MA, hold N days) ---

def run_momentum(
    ohlcv: List[Dict[str, Any]],
    symbol: str,
    lookback: int = 20,
    hold_days: int = 5,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Long when close > MA(lookback); hold for hold_days then exit."""
    df = _ensure_dataframe(ohlcv)
    if df.empty or len(df) < lookback + hold_days:
        return _empty_result(symbol, ohlcv, initial_capital)

    df["ma"] = df["close"].rolling(lookback).mean()
    df["signal"] = (df["close"] > df["ma"]).astype(int)
    df["position"] = df["signal"].diff().fillna(0)

    trades: List[Trade] = []
    in_position = False
    entry_time = None
    entry_price = None
    exit_countdown = None

    for i in range(lookback, len(df)):
        idx = df.index[i]
        if not in_position and df.iloc[i]["position"] == 1:
            in_position = True
            entry_time = idx
            entry_price = float(df.iloc[i]["close"])
            exit_countdown = hold_days
        if in_position:
            exit_countdown -= 1
            if exit_countdown <= 0:
                exit_price = float(df.iloc[i]["close"])
                pnl = exit_price - entry_price
                pnl_pct = (exit_price / entry_price - 1) * 100
                trades.append(Trade(
                    entry_date=str(entry_time.date()),
                    exit_date=str(idx.date()),
                    entry_price=entry_price,
                    exit_price=exit_price,
                    side="long",
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    hold_bars=hold_days,
                ))
                in_position = False

    return _build_result(df, trades, symbol, initial_capital, ohlcv)


# --- Strategy: Mean Reversion (RSI oversold / overbought) ---

def run_mean_reversion(
    ohlcv: List[Dict[str, Any]],
    symbol: str,
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Long when RSI < oversold; exit when RSI > overbought or opposite signal."""
    df = _ensure_dataframe(ohlcv)
    if df.empty or len(df) < rsi_period + 1:
        return _empty_result(symbol, ohlcv, initial_capital)

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(rsi_period).mean()
    avg_loss = loss.rolling(rsi_period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))

    trades: List[Trade] = []
    in_position = False
    entry_time = None
    entry_price = None

    for i in range(rsi_period, len(df)):
        idx = df.index[i]
        rsi = df.iloc[i]["rsi"]
        if not in_position and rsi < oversold:
            in_position = True
            entry_time = idx
            entry_price = float(df.iloc[i]["close"])
        elif in_position and (rsi > overbought or rsi < oversold):
            exit_price = float(df.iloc[i]["close"])
            pnl = exit_price - entry_price
            pnl_pct = (exit_price / entry_price - 1) * 100
            trades.append(Trade(
                entry_date=str(entry_time.date()),
                exit_date=str(idx.date()),
                entry_price=entry_price,
                exit_price=exit_price,
                side="long",
                pnl=pnl,
                pnl_pct=pnl_pct,
                hold_bars=df.index.get_loc(idx) - df.index.get_loc(entry_time),
            ))
            in_position = False
            if rsi < oversold:
                in_position = True
                entry_time = idx
                entry_price = exit_price

    return _build_result(df, trades, symbol, initial_capital, ohlcv)


def _empty_result(symbol: str, ohlcv: List[Dict[str, Any]], initial_capital: float) -> BacktestResult:
    start = ohlcv[0]["date"] if ohlcv else ""
    end = ohlcv[-1]["date"] if ohlcv else ""
    return BacktestResult(
        symbol=symbol,
        start_date=start,
        end_date=end,
        initial_capital=initial_capital,
        final_equity=initial_capital,
        total_return_pct=0.0,
        sharpe_ratio=None,
        max_drawdown_pct=0.0,
        win_rate_pct=0.0,
        num_trades=0,
        equity_curve=[],
        trades=[],
    )


def _build_result(
    df: pd.DataFrame,
    trades: List[Trade],
    symbol: str,
    initial_capital: float,
    ohlcv: List[Dict[str, Any]],
) -> BacktestResult:
    if not ohlcv:
        return _empty_result(symbol, ohlcv, initial_capital)
    start_date = ohlcv[0]["date"]
    end_date = ohlcv[-1]["date"]

    # Equity curve: assume equal capital per trade, no compounding for simplicity
    equity = initial_capital
    trade_pnls = [t.pnl_pct for t in trades]
    for pct in trade_pnls:
        equity *= (1 + pct / 100)
    final_equity = equity
    total_return_pct = (final_equity / initial_capital - 1) * 100

    # Per-bar equity for curve (simplified: linear interpolation by trade count)
    equity_curve_series = pd.Series(index=df.index, dtype=float)
    equity_curve_series.iloc[0] = initial_capital
    if trades:
        step = (final_equity - initial_capital) / max(len(df), 1)
        for i in range(1, len(equity_curve_series)):
            equity_curve_series.iloc[i] = equity_curve_series.iloc[i - 1] + step
        equity_curve_series.iloc[-1] = final_equity
    else:
        equity_curve_series = equity_curve_series.ffill().fillna(initial_capital)
    equity_curve = _compute_equity_curve(equity_curve_series.ffill().fillna(initial_capital))

    returns = pd.Series([t.pnl_pct / 100 for t in trades])
    sharpe = _compute_sharpe(returns) if len(returns) > 1 else None
    max_dd = _compute_max_drawdown(equity_curve_series) if not equity_curve_series.empty else 0.0

    wins = sum(1 for t in trades if t.pnl > 0)
    win_rate_pct = (wins / len(trades) * 100) if trades else 0.0

    trades_dict = [
        {
            "entry_date": t.entry_date,
            "exit_date": t.exit_date,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "side": t.side,
            "pnl": t.pnl,
            "pnl_pct": t.pnl_pct,
            "hold_bars": t.hold_bars,
        }
        for t in trades
    ]

    return BacktestResult(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        final_equity=final_equity,
        total_return_pct=total_return_pct,
        sharpe_ratio=sharpe,
        max_drawdown_pct=max_dd,
        win_rate_pct=win_rate_pct,
        num_trades=len(trades),
        equity_curve=equity_curve,
        trades=trades_dict,
    )


def run_backtest(
    strategy_type: str,
    ohlcv: List[Dict[str, Any]],
    symbol: str,
    params: Optional[Dict[str, Any]] = None,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Dispatch to the correct strategy."""
    params = params or {}
    if strategy_type == "ma_crossover":
        return run_ma_crossover(
            ohlcv, symbol,
            fast_period=int(params.get("fast_period", 10)),
            slow_period=int(params.get("slow_period", 30)),
            initial_capital=initial_capital,
        )
    if strategy_type == "momentum":
        return run_momentum(
            ohlcv, symbol,
            lookback=int(params.get("lookback", 20)),
            hold_days=int(params.get("hold_days", 5)),
            initial_capital=initial_capital,
        )
    if strategy_type == "mean_reversion":
        return run_mean_reversion(
            ohlcv, symbol,
            rsi_period=int(params.get("rsi_period", 14)),
            oversold=float(params.get("oversold", 30)),
            overbought=float(params.get("overbought", 70)),
            initial_capital=initial_capital,
        )
    raise ValueError(f"Unknown strategy type: {strategy_type}")
