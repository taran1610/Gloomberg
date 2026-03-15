"""
EDGAR helper using edgartools for SEC data.
Provides shares_outstanding, public_float for ownership; Form 4 insider transactions;
and debt/liabilities from 10-K/10-Q balance sheets.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_edgar_available = False
try:
    from edgar import Company, set_identity
    _edgar_available = True
except ImportError:
    pass


def init_edgar(identity: str) -> None:
    """Set SEC-required identity. Call at app startup."""
    if _edgar_available and identity:
        try:
            set_identity(identity)
            logger.info("EDGAR identity set for SEC requests")
        except Exception as e:
            logger.warning(f"Could not set EDGAR identity: {e}")


def get_ownership_from_edgar(ticker: str) -> Optional[dict]:
    """
    Get shares_outstanding and public_float from SEC via edgartools.
    Returns {"shares_outstanding": float, "public_float": float} or None.
    """
    if not _edgar_available:
        return None
    try:
        company = Company(ticker)
        if company.not_found:
            return None
        so = company.shares_outstanding
        pf = company.public_float
        if so is None and pf is None:
            return None
        return {
            "shares_outstanding": float(so) if so is not None else None,
            "public_float": float(pf) if pf is not None else None,
        }
    except Exception as e:
        logger.debug(f"edgartools ownership for {ticker}: {e}")
        return None


def get_insider_transactions_from_edgar(ticker: str, limit: int = 50) -> Optional[dict]:
    """
    Get insider transactions from Form 4 filings via edgartools.
    Returns {"ticker": str, "transactions": int, "buys": int, "sells": int, "insider_transactions": list}
    or None on failure.
    """
    if not _edgar_available:
        return None
    try:
        company = Company(ticker)
        if company.not_found:
            return None
        filings = company.get_filings(form="4")
        if not filings or len(filings) == 0:
            return {"ticker": ticker.upper(), "transactions": 0, "buys": 0, "sells": 0, "insider_transactions": []}

        records = []
        buys = 0
        sells = 0
        for filing in filings.head(20):
            if len(records) >= limit:
                break
            try:
                obj = filing.obj()
                if obj is None:
                    continue
                df = obj.to_dataframe()
                if df is None or df.empty:
                    continue
                col_lower = {str(c).lower(): c for c in df.columns}
                for _, row in df.iterrows():
                    if len(records) >= limit:
                        break
                    def _get(*keys):
                        for k in keys:
                            c = col_lower.get(k.lower())
                            if c and c in row.index:
                                v = row[c]
                                return v if v is not None and str(v) != "nan" else None
                        return None
                    insider_name = str(_get("owner_name", "reporting_owner", "name") or "")
                    title = str(_get("officer_title", "relationship", "title") or "")
                    trans_date = str(_get("transaction_date", "date") or "")[:10]
                    shares_val = _get("shares", "amount", "quantity")
                    try:
                        shares = int(float(shares_val or 0))
                    except (ValueError, TypeError):
                        shares = 0
                    if shares > 0:
                        buys += 1
                    elif shares < 0:
                        sells += 1
                    value = _get("value", "value_usd", "acquisition_disposition_value")
                    try:
                        value = float(value) if value is not None else None
                    except (ValueError, TypeError):
                        value = None
                    price = round(abs(value / shares), 2) if value and shares else None
                    records.append({
                        "insider_name": insider_name or "Unknown",
                        "title": title or "",
                        "trans_date": trans_date or "",
                        "shares": shares,
                        "price": price,
                        "value": value,
                    })
            except Exception as e:
                logger.debug(f"edgartools Form 4 parse: {e}")
                continue

        return {
            "ticker": ticker.upper(),
            "transactions": len(records),
            "buys": buys,
            "sells": sells,
            "insider_transactions": records[:limit],
        }
    except Exception as e:
        logger.debug(f"edgartools insider for {ticker}: {e}")
        return None


def get_debt_data_from_edgar(ticker: str) -> Optional[dict]:
    """
    Get debt and liabilities from SEC 10-K/10-Q balance sheet via edgartools.
    Returns {"ticker": str, "fiscal_year": str, "items": [{"label": str, "value": float}, ...]}
    or None on failure.
    """
    if not _edgar_available:
        return None
    try:
        company = Company(ticker)
        if company.not_found:
            return None
        financials = company.get_financials()
        if financials is None:
            return None

        # Use convenience methods where available
        total_assets = _safe_float(financials.get_total_assets()) if hasattr(financials, "get_total_assets") else None
        total_liabilities = _safe_float(financials.get_total_liabilities()) if hasattr(financials, "get_total_liabilities") else None
        current_liabilities = _safe_float(financials.get_current_liabilities()) if hasattr(financials, "get_current_liabilities") else None
        stockholders_equity = _safe_float(financials.get_stockholders_equity()) if hasattr(financials, "get_stockholders_equity") else None

        # Parse balance sheet DataFrame for debt-specific line items
        total_debt = None
        current_debt = None
        long_term_debt = None
        noncurrent_liabilities = None
        fiscal_year = ""

        try:
            bs = financials.balance_sheet()
            if bs is not None:
                df = bs.to_dataframe() if hasattr(bs, "to_dataframe") else None
                if df is not None and not df.empty:
                    # Get fiscal year from first column
                    if len(df.columns) > 0:
                        col = df.columns[0]
                        if hasattr(col, "strftime"):
                            fiscal_year = str(col.strftime("%Y")) + "-FY"
                        else:
                            fiscal_year = str(col)[:7] if col else ""

                    def _find_value(*labels: str) -> Optional[float]:
                        for idx in df.index:
                            parts = (idx,) if not isinstance(idx, tuple) else idx
                            idx_str = " ".join(str(p) for p in parts).lower()
                            for label in labels:
                                if label.lower() in idx_str:
                                    try:
                                        val = df.loc[idx, df.columns[0]]
                                        return _safe_float(val)
                                    except (KeyError, TypeError):
                                        pass
                        return None

                    total_debt = _find_value("Total Debt", "Debt, Current And Noncurrent")
                    current_debt = _find_value(
                        "Current Debt", "Current Portion", "Short-term Debt",
                        "Debt Current"
                    )
                    long_term_debt = _find_value("Long-term Debt", "Long Term Debt", "Debt Noncurrent")
                    noncurrent_liabilities = _find_value(
                        "Total Noncurrent Liabilities", "Noncurrent Liabilities",
                        "Long-term Liabilities"
                    )

                    # Fallback: compute total_debt from components
                    if total_debt is None and (current_debt is not None or long_term_debt is not None):
                        total_debt = (current_debt or 0) + (long_term_debt or 0)
                        if total_debt == 0:
                            total_debt = None
        except Exception as e:
            logger.debug(f"edgartools balance_sheet parse for {ticker}: {e}")

        items = [
            {"label": "Total Debt", "value": total_debt},
            {"label": "Current Debt (Due < 1yr)", "value": current_debt},
            {"label": "Long-Term Debt", "value": long_term_debt},
            {"label": "Total Liabilities", "value": total_liabilities},
            {"label": "Current Liabilities", "value": current_liabilities},
            {"label": "Non-Current Liabilities", "value": noncurrent_liabilities},
            {"label": "Total Assets", "value": total_assets},
            {"label": "Shareholders' Equity", "value": stockholders_equity},
        ]

        # Ratios
        debt_equity = None
        debt_assets = None
        liab_assets = None
        if total_debt and stockholders_equity and stockholders_equity != 0:
            debt_equity = round(total_debt / stockholders_equity * 100, 1)
        if total_debt and total_assets and total_assets != 0:
            debt_assets = round(total_debt / total_assets * 100, 1)
        if total_liabilities and total_assets and total_assets != 0:
            liab_assets = round(total_liabilities / total_assets * 100, 1)

        items.extend([
            {"label": "Debt / Equity Ratio", "value": debt_equity},
            {"label": "Debt / Assets Ratio", "value": debt_assets},
            {"label": "Liabilities / Assets", "value": liab_assets},
        ])

        # Only return if we have meaningful data
        if not any(i.get("value") for i in items):
            return None

        return {
            "ticker": ticker.upper(),
            "fiscal_year": fiscal_year,
            "items": items,
        }
    except Exception as e:
        logger.debug(f"edgartools debt for {ticker}: {e}")
        return None


def _safe_float(val) -> Optional[float]:
    """Convert value to float, return None on failure."""
    if val is None or str(val) == "nan":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
