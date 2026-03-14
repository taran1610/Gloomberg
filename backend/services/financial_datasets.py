"""
Financial Datasets API client — the same institutional-grade data source
that powers virattt/dexter. Provides income statements, balance sheets,
cash flow, key ratios, analyst estimates, stock prices, company news,
insider trades, and segmented revenue.

API docs: https://docs.financialdatasets.ai
Free tickers: AAPL, NVDA, MSFT (no key required).
"""

import logging
from typing import Any, Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.financialdatasets.ai"


class FinancialDatasetsClient:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.financial_datasets_api_key
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        client = self._get_client()
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        resp = await client.get(path, params=clean)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Financial Statements
    # ------------------------------------------------------------------

    async def get_income_statements(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4,
        **date_filters: str,
    ) -> dict:
        params = {"ticker": ticker, "period": period, "limit": limit, **date_filters}
        data = await self._get("/financials/income-statements/", params)
        return {
            "tool": "get_income_statements",
            "ticker": ticker,
            "data": data.get("income_statements", []),
        }

    async def get_balance_sheets(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4,
        **date_filters: str,
    ) -> dict:
        params = {"ticker": ticker, "period": period, "limit": limit, **date_filters}
        data = await self._get("/financials/balance-sheets/", params)
        return {
            "tool": "get_balance_sheets",
            "ticker": ticker,
            "data": data.get("balance_sheets", []),
        }

    async def get_cash_flow_statements(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4,
        **date_filters: str,
    ) -> dict:
        params = {"ticker": ticker, "period": period, "limit": limit, **date_filters}
        data = await self._get("/financials/cash-flow-statements/", params)
        return {
            "tool": "get_cash_flow_statements",
            "ticker": ticker,
            "data": data.get("cash_flow_statements", []),
        }

    async def get_all_financials(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4,
        **date_filters: str,
    ) -> dict:
        params = {"ticker": ticker, "period": period, "limit": limit, **date_filters}
        data = await self._get("/financials/", params)
        return {
            "tool": "get_all_financials",
            "ticker": ticker,
            "data": data.get("financials", []),
        }

    # ------------------------------------------------------------------
    # Key Ratios & Metrics
    # ------------------------------------------------------------------

    async def get_key_ratios(self, ticker: str, period: str = "annual", limit: int = 1) -> dict:
        params = {"ticker": ticker, "period": period, "limit": limit}
        data = await self._get("/financial-metrics/", params)
        return {
            "tool": "get_key_ratios",
            "ticker": ticker,
            "data": data.get("financial_metrics", []),
        }

    # ------------------------------------------------------------------
    # Analyst Estimates
    # ------------------------------------------------------------------

    async def get_analyst_estimates(self, ticker: str, period: str = "annual", limit: int = 4) -> dict:
        params = {"ticker": ticker, "period": period, "limit": limit}
        data = await self._get("/analyst-estimates/", params)
        return {
            "tool": "get_analyst_estimates",
            "ticker": ticker,
            "data": data.get("analyst_estimates", []),
        }

    # ------------------------------------------------------------------
    # Prices
    # ------------------------------------------------------------------

    async def get_stock_price(self, ticker: str) -> dict:
        data = await self._get("/prices/snapshot/", {"ticker": ticker})
        return {
            "tool": "get_stock_price",
            "ticker": ticker,
            "data": data.get("snapshot", {}),
        }

    async def get_stock_prices(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = "day",
        limit: int = 252,
    ) -> dict:
        params = {
            "ticker": ticker,
            "interval": interval,
            "limit": limit,
            "start_date": start_date,
            "end_date": end_date,
        }
        data = await self._get("/prices/", params)
        return {
            "tool": "get_stock_prices",
            "ticker": ticker,
            "data": data.get("prices", []),
        }

    # ------------------------------------------------------------------
    # Company News
    # ------------------------------------------------------------------

    async def get_company_news(self, ticker: str, limit: int = 10) -> dict:
        params = {"ticker": ticker, "limit": limit}
        data = await self._get("/news/", params)
        return {
            "tool": "get_company_news",
            "ticker": ticker,
            "data": data.get("news", []),
        }

    # ------------------------------------------------------------------
    # Insider Trades
    # ------------------------------------------------------------------

    async def get_insider_trades(self, ticker: str, limit: int = 20) -> dict:
        params = {"ticker": ticker, "limit": limit}
        data = await self._get("/insider-trades/", params)
        return {
            "tool": "get_insider_trades",
            "ticker": ticker,
            "data": data.get("insider_trades", []),
        }

    # ------------------------------------------------------------------
    # Segmented Revenue
    # ------------------------------------------------------------------

    async def get_segmented_revenues(self, ticker: str, period: str = "annual", limit: int = 4) -> dict:
        params = {"ticker": ticker, "period": period, "limit": limit}
        data = await self._get("/segmented-revenues/", params)
        return {
            "tool": "get_segmented_revenues",
            "ticker": ticker,
            "data": data.get("segmented_revenues", []),
        }

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
