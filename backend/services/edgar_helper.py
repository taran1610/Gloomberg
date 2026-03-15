"""
EDGAR helper using edgartools for SEC data.
Provides shares_outstanding, public_float for ownership, and Form 4 insider transactions.
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
