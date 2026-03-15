"""
Compute correlation and linear regression between an asset and a benchmark (SPY).
Returns scatter points, regression stats, and normalized overlay data.
Uses fetch_history_df_with_fallback (yfinance + akshare) to avoid Yahoo rate limits.
"""
import pandas as pd
import numpy as np
import logging

from services.data_sources import fetch_history_df_with_fallback

logger = logging.getLogger(__name__)

BENCHMARK = "SPY"
DEFAULT_PERIOD = "1y"


def _daily_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily OHLCV to weekly (Friday close)."""
    if df is None or df.empty or "Close" not in df.columns:
        return pd.DataFrame()
    w = df.resample("W-FRI").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna(subset=["Close"])
    return w


def compute_weekly_returns(ticker: str, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    """Fetch weekly OHLC and compute weekly % returns for ticker and benchmark.
    Uses akshare fallback for US stocks when yfinance is rate limited."""
    try:
        df_t = fetch_history_df_with_fallback(ticker, period)
        df_b = fetch_history_df_with_fallback(BENCHMARK, period)

        if df_t is None or df_t.empty or df_b is None or df_b.empty:
            return pd.DataFrame()

        df_t = _daily_to_weekly(df_t)
        df_b = _daily_to_weekly(df_b)

        if len(df_t) < 5 or len(df_b) < 5:
            return pd.DataFrame()

        df_t["ret"] = df_t["Close"].pct_change() * 100
        df_b["ret"] = df_b["Close"].pct_change() * 100

        common = df_t.index.intersection(df_b.index)
        df_t = df_t.loc[common].dropna(subset=["ret"])
        df_b = df_b.loc[common].reindex(df_t.index).dropna(subset=["ret"])
        common = df_t.index.intersection(df_b.index)
        df_t = df_t.loc[common]
        df_b = df_b.loc[common]

        out = pd.DataFrame(
            {
                "date": common.strftime("%Y-%m-%d"),
                "ticker_ret": df_t["ret"].values,
                "bench_ret": df_b["ret"].values,
                "ticker_close": df_t["Close"].values,
                "bench_close": df_b["Close"].values,
            },
            index=common,
        )
        return out.dropna()
    except Exception as e:
        logger.error(f"Correlation compute error: {e}")
        return pd.DataFrame()


def linear_regression(y: np.ndarray, x: np.ndarray) -> dict:
    """OLS: y = alpha + beta * x. Returns alpha, beta, r_sq, r, std_err, etc."""
    n = len(y)
    if n < 3:
        return {}

    x_mean = np.mean(x)
    y_mean = np.mean(y)
    ss_xx = np.sum((x - x_mean) ** 2)
    ss_yy = np.sum((y - y_mean) ** 2)
    ss_xy = np.sum((x - x_mean) * (y - y_mean))

    beta = ss_xy / ss_xx if ss_xx != 0 else 0
    alpha = y_mean - beta * x_mean

    y_hat = alpha + beta * x
    residuals = y - y_hat
    ss_res = np.sum(residuals ** 2)
    ss_tot = ss_yy
    r_sq = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    r = np.sign(beta) * np.sqrt(max(0, r_sq))

    mse = ss_res / (n - 2) if n > 2 else 0
    std_err = np.sqrt(mse)
    std_err_alpha = std_err * np.sqrt(1 / n + x_mean ** 2 / ss_xx) if ss_xx != 0 else 0
    std_err_beta = std_err / np.sqrt(ss_xx) if ss_xx != 0 else 0

    t_alpha = alpha / std_err_alpha if std_err_alpha != 0 else 0
    t_beta = beta / std_err_beta if std_err_beta != 0 else 0

    adjusted_beta = (2 / 3) * beta + (1 / 3) * 1.0

    last_y = y[-1] if len(y) > 0 else 0
    last_x = x[-1] if len(x) > 0 else 0
    last_spread = last_y - (alpha + beta * last_x)
    last_ratio = last_y / last_x if last_x != 0 else 0

    return {
        "raw_beta": round(beta, 4),
        "adjusted_beta": round(adjusted_beta, 4),
        "alpha": round(alpha, 4),
        "r_sq": round(r_sq, 4),
        "r": round(r, 4),
        "std_dev_error": round(std_err, 4),
        "std_err_alpha": round(std_err_alpha, 4),
        "std_err_beta": round(std_err_beta, 4),
        "t_test_alpha": round(t_alpha, 4),
        "significance": "<0.001" if abs(t_beta) > 3.5 else ">0.05",
        "last_t_value": round(t_beta, 4),
        "last_p_value": round(0.5, 3),
        "num_points": n,
        "last_spread": round(last_spread, 4),
        "last_ratio": round(last_ratio, 4),
    }


def get_rel_index_data(ticker: str, period: str = "1y") -> dict:
    """Return scatter points, regression stats, and normalized overlay for REL INDEX tab."""
    df = compute_weekly_returns(ticker, period)
    if df.empty:
        return {"error": "Insufficient data"}

    y = df["ticker_ret"].values
    x = df["bench_ret"].values

    stats = linear_regression(y, x)
    if not stats:
        return {"error": "Regression failed"}

    scatter = [
        {"x": float(xi), "y": float(yi), "date": str(d)}
        for xi, yi, d in zip(x, y, df["date"])
    ]

    beta = stats["raw_beta"]
    alpha = stats["alpha"]
    reg_line = [{"x": float(xi), "y": float(alpha + beta * xi)} for xi in x]

    base_t = df["ticker_close"].iloc[0]
    base_b = df["bench_close"].iloc[0]
    norm_ticker = (df["ticker_close"].values / base_t * 100).tolist()
    norm_bench = (df["bench_close"].values / base_b * 100).tolist()
    dates = df["date"].tolist()

    overlay = [
        {"date": d, "ticker": round(t, 2), "benchmark": round(b, 2)}
        for d, t, b in zip(dates, norm_ticker, norm_bench)
    ]

    start_date = dates[0] if dates else ""
    end_date = dates[-1] if dates else ""

    return {
        "ticker": ticker.upper(),
        "benchmark": BENCHMARK,
        "benchmark_name": "S&P 500 INDEX (SPY)",
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "scatter": scatter,
        "regression_line": reg_line,
        "equation": f"Y = {beta:.3f} * X + {alpha:.3f}",
        "stats": stats,
        "overlay": overlay,
    }
