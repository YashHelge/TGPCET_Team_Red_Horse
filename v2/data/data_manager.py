"""
TradeOS V2 — Unified Data Manager
Central access point for all market data with intelligent routing,
caching, rate-limit coordination, and API fallback.
"""

import asyncio
import logging
import time
from typing import Optional

import pandas as pd

from v2.config.settings import settings
from v2.data.realtime_scraper import MarketDataScraper
from v2.data.historical import HistoricalDataClient
from v2.data.stock_universe import STOCK_UNIVERSE, get_stock_info

logger = logging.getLogger("tradeos.data_manager")


class DataManager:
    """
    Unified data access layer.
    - Real-time quotes via scraper (Google Finance → Yahoo → Finnhub)
    - Historical OHLCV via yfinance
    - Fundamental data via FMP / Alpha Vantage
    - In-memory cache with TTL per data type
    """

    def __init__(self):
        self.scraper = MarketDataScraper(
            finnhub_key=settings.FINNHUB_API_KEY,
            cache_ttl=settings.CACHE_TTL_REALTIME,
        )
        self.historical = HistoricalDataClient(
            cache_ttl=settings.CACHE_TTL_HISTORICAL,
        )
        self._fundamental_cache: dict[str, tuple[dict, float]] = {}
        self._news_cache: dict[str, tuple[list, float]] = {}

    # ── Real-Time Quotes ────────────────────────────────────────

    async def get_quote(self, symbol: str) -> dict:
        """Get real-time quote with auto-fallback."""
        quote = await self.scraper.get_quote(symbol)
        # Enrich with name/sector from universe
        info = get_stock_info(symbol)
        if info:
            quote["name"] = info["name"]
            quote["sector"] = info["sector"]
            quote["exchange"] = info["exchange"]
        else:
            quote["name"] = symbol
            quote["sector"] = "Unknown"
            quote["exchange"] = "Unknown"
        return quote

    async def get_batch_quotes(self, symbols: list[str], concurrency: int = 8) -> list[dict]:
        """Batch fetch quotes with controlled concurrency."""
        quotes = await self.scraper.get_batch_quotes(symbols, concurrency)
        for q in quotes:
            info = get_stock_info(q.get("symbol", ""))
            if info:
                q["name"] = info["name"]
                q["sector"] = info["sector"]
                q["exchange"] = info["exchange"]
        return quotes

    # ── Historical Data ─────────────────────────────────────────

    def get_historical(
        self, symbol: str, period_days: int = 365, interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical OHLCV data."""
        return self.historical.fetch(symbol, period_days, interval)

    def get_multi_timeframe(self, symbol: str) -> dict[str, pd.DataFrame]:
        """Get 15min, 1h, daily data for multi-timeframe analysis."""
        return self.historical.fetch_multi_timeframe(symbol)

    def get_sector_returns(self, sector: str, period_days: int = 365) -> pd.DataFrame:
        """Get returns matrix for a sector (for herding detection)."""
        from v2.data.stock_universe import get_sector_stocks
        sector_stocks = get_sector_stocks(sector)
        symbols = [s["symbol"] for s in sector_stocks]
        return self.historical.get_returns_matrix(symbols, period_days)

    # ── Fundamentals ────────────────────────────────────────────

    async def get_fundamentals(self, symbol: str) -> dict:
        """Get fundamental data (P/E, EPS, revenue, etc.)."""
        # Check cache
        if symbol in self._fundamental_cache:
            data, ts = self._fundamental_cache[symbol]
            if time.time() - ts < settings.CACHE_TTL_FUNDAMENTALS:
                return data

        fundamentals = await self._fetch_fundamentals(symbol)
        self._fundamental_cache[symbol] = (fundamentals, time.time())
        return fundamentals

    async def _fetch_fundamentals(self, symbol: str) -> dict:
        """Fetch fundamentals from FMP API or fallback to yfinance."""
        # Try FMP first
        if settings.FMP_API_KEY:
            try:
                import httpx
                clean = symbol.replace(".NS", "").replace(".BO", "")
                async with httpx.AsyncClient(timeout=10) as client:
                    # Key Metrics
                    resp = await client.get(
                        f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{clean}",
                        params={"apikey": settings.FMP_API_KEY}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            m = data[0]
                            return {
                                "peRatio": round(float(m.get("peRatioTTM", 0) or 0), 2),
                                "pbRatio": round(float(m.get("pbRatioTTM", 0) or 0), 2),
                                "psRatio": round(float(m.get("priceToSalesRatioTTM", 0) or 0), 2),
                                "epsGrowth": round(float(m.get("epsgrowth", 0) or 0), 2),
                                "revenueGrowth": round(float(m.get("revenuePerShareTTM", 0) or 0), 2),
                                "debtEquity": round(float(m.get("debtToEquityTTM", 0) or 0), 2),
                                "fcfYield": round(float(m.get("freeCashFlowYieldTTM", 0) or 0), 4),
                                "roe": round(float(m.get("roeTTM", 0) or 0), 4),
                                "roce": round(float(m.get("returnOnCapitalEmployedTTM", 0) or 0), 4),
                                "dividendYield": round(float(m.get("dividendYieldTTM", 0) or 0), 4),
                                "source": "fmp",
                            }
            except Exception as e:
                logger.debug(f"FMP fundamentals failed for {symbol}: {e}")

        # Fallback: yfinance
        try:
            import yfinance as yf
            t = yf.Ticker(symbol)
            info = t.info
            return {
                "peRatio": round(float(info.get("trailingPE", 0) or 0), 2),
                "pbRatio": round(float(info.get("priceToBook", 0) or 0), 2),
                "psRatio": round(float(info.get("priceToSalesTrailing12Months", 0) or 0), 2),
                "epsGrowth": round(float(info.get("earningsQuarterlyGrowth", 0) or 0), 2),
                "revenueGrowth": round(float(info.get("revenueGrowth", 0) or 0), 2),
                "debtEquity": round(float(info.get("debtToEquity", 0) or 0), 2),
                "fcfYield": round(float(info.get("freeCashflow", 0) or 0) / max(float(info.get("marketCap", 1) or 1), 1), 4),
                "roe": round(float(info.get("returnOnEquity", 0) or 0), 4),
                "roce": 0,  # Not available from yfinance
                "dividendYield": round(float(info.get("dividendYield", 0) or 0), 4),
                "source": "yfinance",
            }
        except Exception as e:
            logger.debug(f"yfinance fundamentals failed for {symbol}: {e}")
            return {k: 0 for k in ["peRatio", "pbRatio", "psRatio", "epsGrowth",
                                    "revenueGrowth", "debtEquity", "fcfYield",
                                    "roe", "roce", "dividendYield"]}

    # ── News ────────────────────────────────────────────────────

    async def get_news(self, symbol: str, limit: int = 20) -> list[dict]:
        """Fetch news for a symbol from Finnhub."""
        if symbol in self._news_cache:
            data, ts = self._news_cache[symbol]
            if time.time() - ts < settings.CACHE_TTL_NEWS:
                return data

        news = await self._fetch_news(symbol, limit)
        self._news_cache[symbol] = (news, time.time())
        return news

    async def _fetch_news(self, symbol: str, limit: int = 20) -> list[dict]:
        """Fetch news from Finnhub API."""
        if not settings.FINNHUB_API_KEY:
            return []
        try:
            import httpx
            from datetime import datetime, timedelta
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            clean = symbol.replace(".NS", "").replace(".BO", "").replace(".L", "").replace(".DE", "")

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://finnhub.io/api/v1/company-news",
                    params={
                        "symbol": clean,
                        "from": start,
                        "to": end,
                        "token": settings.FINNHUB_API_KEY,
                    }
                )
                if resp.status_code == 200:
                    articles = resp.json()[:limit]
                    return [
                        {
                            "title": a.get("headline", ""),
                            "summary": a.get("summary", ""),
                            "source": a.get("source", ""),
                            "url": a.get("url", ""),
                            "datetime": a.get("datetime", 0),
                            "category": a.get("category", ""),
                        }
                        for a in articles
                    ]
        except Exception as e:
            logger.debug(f"News fetch failed for {symbol}: {e}")
        return []

    # ── Market Status ───────────────────────────────────────────

    def get_market_status(self, exchange: str) -> dict:
        """Check if a market is currently open."""
        from datetime import datetime
        import pytz

        hours = settings.MARKET_HOURS.get(exchange)
        if not hours:
            return {"exchange": exchange, "status": "unknown"}

        try:
            tz = pytz.timezone(hours["tz"])
            now = datetime.now(tz)
            open_time = datetime.strptime(hours["open"], "%H:%M").time()
            close_time = datetime.strptime(hours["close"], "%H:%M").time()
            is_weekday = now.weekday() < 5
            is_open = is_weekday and open_time <= now.time() <= close_time

            return {
                "exchange": exchange,
                "status": "open" if is_open else "closed",
                "localTime": now.strftime("%H:%M:%S"),
                "openTime": hours["open"],
                "closeTime": hours["close"],
                "timezone": hours["tz"],
            }
        except Exception:
            return {"exchange": exchange, "status": "unknown"}

    # ── Cleanup ─────────────────────────────────────────────────

    async def cleanup(self):
        await self.scraper.close()


# Singleton
data_manager = DataManager()
