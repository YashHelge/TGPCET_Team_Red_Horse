"""
TradeOS V2 — Historical Data Client
Fetches OHLCV data from yfinance for ML training and indicator computation.
Supports multi-timeframe (15min, 1h, 1d) and batch downloads.
"""

import logging
import time
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("tradeos.historical")


class HistoricalDataClient:
    """
    Historical OHLCV data provider using yfinance.
    - In-memory cache with TTL
    - Multi-timeframe support
    - Batch sector downloads
    """

    def __init__(self, cache_ttl: int = 3600):
        self._cache: dict[str, tuple[pd.DataFrame, float]] = {}
        self._cache_ttl = cache_ttl

    def _cache_key(self, symbol: str, period_days: int, interval: str) -> str:
        return f"{symbol}_{period_days}_{interval}"

    def fetch(
        self,
        symbol: str,
        period_days: int = 365,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data with computed returns.
        Intervals: 1m, 5m, 15m, 30m, 1h, 1d, 1wk
        """
        key = self._cache_key(symbol, period_days, interval)
        if key in self._cache:
            df, ts = self._cache[key]
            if time.time() - ts < self._cache_ttl and not df.empty:
                return df.copy()

        try:
            import yfinance as yf
            end = datetime.now()
            start = end - timedelta(days=period_days)

            # yfinance limits intraday data periods
            if interval in ("1m", "5m"):
                start = max(start, end - timedelta(days=7))
            elif interval in ("15m", "30m"):
                start = max(start, end - timedelta(days=60))
            elif interval == "1h":
                start = max(start, end - timedelta(days=730))

            t = yf.Ticker(symbol)
            df = t.history(start=start, end=end, interval=interval)

            if df.empty:
                return pd.DataFrame()

            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df["Returns"] = df["Close"].pct_change(fill_method=None)
            df["LogReturns"] = np.log(df["Close"] / df["Close"].shift(1))
            df.dropna(subset=["Returns"], inplace=True)

            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            self._cache[key] = (df, time.time())
            return df.copy()

        except Exception as e:
            logger.error(f"Historical fetch failed for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_multi_timeframe(self, symbol: str) -> dict[str, pd.DataFrame]:
        """Fetch 15min, 1h, and daily data for multi-timeframe analysis."""
        return {
            "15m": self.fetch(symbol, period_days=60, interval="15m"),
            "1h": self.fetch(symbol, period_days=365, interval="1h"),
            "1d": self.fetch(symbol, period_days=365 * 2, interval="1d"),
        }

    def fetch_batch(self, symbols: list[str], period_days: int = 365) -> dict[str, pd.DataFrame]:
        """Batch fetch for multiple symbols."""
        results = {}
        for sym in symbols:
            df = self.fetch(sym, period_days)
            if not df.empty:
                results[sym] = df
        return results

    def get_returns_matrix(self, symbols: list[str], period_days: int = 365) -> pd.DataFrame:
        """Get returns matrix for sector analysis (herding detection)."""
        returns = {}
        for sym in symbols:
            df = self.fetch(sym, period_days)
            if not df.empty and "Returns" in df.columns:
                returns[sym] = df["Returns"]
        if not returns:
            return pd.DataFrame()
        return pd.DataFrame(returns).dropna()

    def clear_cache(self):
        self._cache.clear()


# Singleton
historical_client = HistoricalDataClient()
