import pandas as pd
import numpy as np
import ta


def compute_indicators(df: pd.DataFrame) -> dict:
    """Compute technical indicators from OHLCV DataFrame."""
    if df.empty or len(df) < 20:
        return {}

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    result = {}

    result["sma_20"] = round(close.rolling(20).mean().iloc[-1], 2) if len(close) >= 20 else None
    result["sma_50"] = round(close.rolling(50).mean().iloc[-1], 2) if len(close) >= 50 else None
    result["sma_200"] = round(close.rolling(200).mean().iloc[-1], 2) if len(close) >= 200 else None

    if len(close) >= 14:
        rsi_indicator = ta.momentum.RSIIndicator(close, window=14)
        rsi_val = rsi_indicator.rsi().iloc[-1]
        result["rsi"] = round(rsi_val, 2) if not np.isnan(rsi_val) else None

    if len(close) >= 26:
        macd_indicator = ta.trend.MACD(close)
        macd_val = macd_indicator.macd().iloc[-1]
        signal_val = macd_indicator.macd_signal().iloc[-1]
        hist_val = macd_indicator.macd_diff().iloc[-1]
        result["macd"] = round(macd_val, 4) if not np.isnan(macd_val) else None
        result["macd_signal"] = round(signal_val, 4) if not np.isnan(signal_val) else None
        result["macd_histogram"] = round(hist_val, 4) if not np.isnan(hist_val) else None

    if len(close) >= 20:
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        result["bb_upper"] = round(bb.bollinger_hband().iloc[-1], 2)
        result["bb_middle"] = round(bb.bollinger_mavg().iloc[-1], 2)
        result["bb_lower"] = round(bb.bollinger_lband().iloc[-1], 2)

    return result


def compute_indicator_series(df: pd.DataFrame) -> pd.DataFrame:
    """Compute full indicator series for backtesting."""
    if df.empty:
        return df

    close = df["Close"]
    df = df.copy()

    for period in [10, 20, 50, 200]:
        if len(close) >= period:
            df[f"SMA_{period}"] = close.rolling(period).mean()

    for period in [10, 20]:
        if len(close) >= period:
            df[f"EMA_{period}"] = close.ewm(span=period, adjust=False).mean()

    if len(close) >= 14:
        df["RSI"] = ta.momentum.RSIIndicator(close, window=14).rsi()

    if len(close) >= 26:
        macd = ta.trend.MACD(close)
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Hist"] = macd.macd_diff()

    if len(close) >= 20:
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        df["BB_Upper"] = bb.bollinger_hband()
        df["BB_Middle"] = bb.bollinger_mavg()
        df["BB_Lower"] = bb.bollinger_lband()

    return df
