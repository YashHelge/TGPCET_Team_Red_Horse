"""
TradeOS V2 — Production-Grade Real-Time Market Data Scraper
Fetches real-time stock quotes from Google Finance + Yahoo Finance with
anti-detection, rotating fingerprints, async concurrency, and auto-fallback.

Architecture:
  Primary   → Google Finance (fastest, structured, no API key)
  Secondary → Yahoo Finance API (yfinance library, reliable batch)
  Tertiary  → Finnhub REST API (rate-limited, US stocks only free)

Anti-Detection:
  - TLS browser impersonation via curl_cffi
  - Rotating User-Agent + correlated headers
  - Random delays with jitter
  - Connection pooling with keep-alive
  - Domain-specific rate limiting
"""

import asyncio
import random
import re
import time
import json
import logging
from typing import Optional
from itertools import cycle
from urllib.parse import quote as url_quote

import httpx

logger = logging.getLogger("tradeos.scraper")

# ─── Browser Fingerprint Profiles ──────────────────────────────
BROWSER_PROFILES = [
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "platform": '"Windows"',
        "accept_lang": "en-US,en;q=0.9",
    },
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "platform": '"macOS"',
        "accept_lang": "en-US,en;q=0.9",
    },
    {
        "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "sec_ch_ua": None,
        "platform": None,
        "accept_lang": "en-US,en;q=0.5",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "sec_ch_ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        "platform": '"Windows"',
        "accept_lang": "en-US,en;q=0.9",
    },
]

REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
]

_profile_pool = cycle(BROWSER_PROFILES)


def _build_headers(profile: dict, referer: str | None = None) -> dict:
    """Build browser-correlated HTTP headers."""
    headers = {
        "User-Agent": profile["ua"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": profile["accept_lang"],
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    if referer:
        headers["Referer"] = referer
    if profile.get("sec_ch_ua"):
        headers["sec-ch-ua"] = profile["sec_ch_ua"]
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = profile["platform"]
        headers["Sec-Fetch-Dest"] = "document"
        headers["Sec-Fetch-Mode"] = "navigate"
        headers["Sec-Fetch-Site"] = "cross-site" if referer else "none"
        headers["Sec-Fetch-User"] = "?1"
    return headers


# ─── Rate Limiter ──────────────────────────────────────────────
class DomainRateLimiter:
    """Per-domain rate limiter to avoid detection."""

    def __init__(self, max_per_minute: int = 20):
        self._timestamps: dict[str, list[float]] = {}
        self._max = max_per_minute
        self._lock = asyncio.Lock()

    async def acquire(self, domain: str):
        async with self._lock:
            now = time.time()
            if domain not in self._timestamps:
                self._timestamps[domain] = []
            # Remove timestamps older than 60s
            self._timestamps[domain] = [t for t in self._timestamps[domain] if now - t < 60]
            if len(self._timestamps[domain]) >= self._max:
                wait = 60 - (now - self._timestamps[domain][0]) + random.uniform(0.5, 2.0)
                if wait > 0:
                    await asyncio.sleep(wait)
            self._timestamps[domain].append(time.time())


_rate_limiter = DomainRateLimiter(max_per_minute=20)


# ─── Google Finance Scraper ────────────────────────────────────

def _gf_symbol(symbol: str) -> str:
    """Convert yfinance symbol to Google Finance format."""
    if symbol.endswith(".NS"):
        return f"{symbol.replace('.NS', '')}:NSE"
    elif symbol.endswith(".BO"):
        return f"{symbol.replace('.BO', '')}:BOM"
    elif symbol.endswith(".L"):
        return f"{symbol.replace('.L', '')}:LON"
    elif symbol.endswith(".DE"):
        return f"{symbol.replace('.DE', '')}:ETR"
    elif symbol.endswith(".T"):
        return f"{symbol.replace('.T', '')}:TYO"
    elif symbol.endswith(".HK"):
        return f"{symbol.replace('.HK', '')}:HKG"
    return f"{symbol}:NYSE"  # default US


async def scrape_google_finance(symbol: str, client: httpx.AsyncClient) -> Optional[dict]:
    """
    Scrape real-time quote from Google Finance.
    Returns dict with price, change, changePct, volume, etc.
    """
    gf_sym = _gf_symbol(symbol)
    url = f"https://www.google.com/finance/quote/{url_quote(gf_sym)}"
    profile = next(_profile_pool)
    headers = _build_headers(profile, random.choice(REFERERS))

    # Google consent cookies to bypass GDPR redirect (302 → consent page)
    cookies = {
        "CONSENT": "PENDING+987",
        "SOCS": "CAISHAgBEhJnd3NfMjAyNDAzMTItMAFIABgAIAE",
    }

    try:
        await _rate_limiter.acquire("google.com")
        await asyncio.sleep(random.uniform(0.2, 0.8))

        resp = await client.get(
            url,
            headers=headers,
            cookies=cookies,
            params={"hl": "en", "gl": "us"},
            timeout=12,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            logger.debug(f"Google Finance returned {resp.status_code} for {symbol}")
            return None

        html = resp.text

        # Extract price from data attribute or structured data
        price = _extract_gf_price(html)
        change, change_pct = _extract_gf_change(html)
        prev_close = _extract_gf_field(html, "Previous close")
        day_range = _extract_gf_field(html, "Day range")
        year_range = _extract_gf_field(html, "Year range")
        volume = _extract_gf_field(html, "Avg Volume") or _extract_gf_field(html, "Volume")
        market_cap = _extract_gf_field(html, "Market cap")
        pe_ratio = _extract_gf_field(html, "P/E ratio")

        if price is None:
            return None

        day_high, day_low = _parse_range(day_range)
        year_high, year_low = _parse_range(year_range)

        return {
            "symbol": symbol,
            "price": price,
            "change": change or 0,
            "changePct": change_pct or 0,
            "prevClose": _parse_number(prev_close) or (price - (change or 0)),
            "volume": _parse_volume(volume),
            "dayHigh": day_high,
            "dayLow": day_low,
            "week52High": year_high,
            "week52Low": year_low,
            "marketCap": _parse_market_cap(market_cap),
            "peRatio": _parse_number(pe_ratio) or 0,
            "source": "google_finance",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.debug(f"Google Finance scrape failed for {symbol}: {e}")
        return None


def _extract_gf_price(html: str) -> float | None:
    """Extract current price from Google Finance HTML."""
    # Method 1: data-last-price attribute
    match = re.search(r'data-last-price="([\d.,]+)"', html)
    if match:
        return _parse_number(match.group(1))
    # Method 2: The main price div
    match = re.search(r'class="YMlKec fxKbKc"[^>]*>([\d,.\s₹$£€¥]+)</div>', html)
    if match:
        return _parse_number(match.group(1))
    # Method 3: AUD format
    match = re.search(r'class="YMlKec fxKbKc"[^>]*>\s*[^\d]*([\d,]+\.?\d*)', html)
    if match:
        return _parse_number(match.group(1))
    return None


def _extract_gf_change(html: str) -> tuple[float | None, float | None]:
    """Extract price change and change percentage."""
    # data attributes
    change_match = re.search(r'data-currency-code="[^"]*"[^>]*data-last-price="[^"]*"[^>]*data-price-change="([^"]*)"[^>]*data-price-change-percent="([^"]*)"', html)
    if change_match:
        return _parse_number(change_match.group(1)), _parse_number(change_match.group(2))
    # Fallback: text-based extraction
    match = re.search(r'class="P2Luy [^"]*"[^>]*><span[^>]*>([+\-−]?[\d.,]+)</span>', html)
    pct_match = re.search(r'class="P2Luy [^"]*"[^>]*>.*?<span[^>]*>\(([+\-−]?[\d.,]+)%\)</span>', html, re.DOTALL)
    change = _parse_number(match.group(1)) if match else None
    pct = _parse_number(pct_match.group(1)) if pct_match else None
    return change, pct


def _extract_gf_field(html: str, field_name: str) -> str | None:
    """Extract a labeled field from Google Finance."""
    pattern = rf'{re.escape(field_name)}</div>\s*<div[^>]*class="P6K39c"[^>]*>(.*?)</div>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        return re.sub(r'<[^>]+>', '', match.group(1)).strip()
    # Alternative structure
    pattern2 = rf'{re.escape(field_name)}\s*</div>\s*<div[^>]*>(.*?)</div>'
    match2 = re.search(pattern2, html, re.DOTALL)
    if match2:
        return re.sub(r'<[^>]+>', '', match2.group(1)).strip()
    return None


def _parse_number(text: str | None) -> float | None:
    """Parse number from text, handling currency symbols and commas."""
    if not text:
        return None
    cleaned = re.sub(r'[₹$£€¥,\s+−]', '', text.replace('−', '-').replace('–', '-'))
    cleaned = cleaned.replace('\u2212', '-')
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_range(text: str | None) -> tuple[float, float]:
    """Parse 'low - high' range string."""
    if not text:
        return 0, 0
    parts = re.split(r'\s*[-–—]\s*', text)
    if len(parts) == 2:
        low = _parse_number(parts[0])
        high = _parse_number(parts[1])
        return high or 0, low or 0
    return 0, 0


def _parse_volume(text: str | None) -> int:
    """Parse volume strings like '1.2M', '500K'."""
    if not text:
        return 0
    text = text.strip().upper().replace(',', '')
    multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000, 'T': 1_000_000_000_000}
    for suffix, mult in multipliers.items():
        if text.endswith(suffix):
            try:
                return int(float(text[:-1]) * mult)
            except ValueError:
                return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def _parse_market_cap(text: str | None) -> float:
    """Parse market cap strings like '2.5T INR'."""
    if not text:
        return 0
    text = text.strip().upper()
    # Remove currency codes
    text = re.sub(r'[A-Z]{3}$', '', text).strip()
    return float(_parse_volume(text)) if text else 0


# ─── Yahoo Finance Fallback (via yfinance) ─────────────────────

def fetch_yahoo_quote(symbol: str) -> Optional[dict]:
    """Synchronous yfinance quote fetch — used as fallback."""
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev = info.get("previousClose", 0)
        if not price:
            return None
        return {
            "symbol": symbol,
            "price": round(float(price), 2),
            "change": round(float(price - prev), 2) if prev else 0,
            "changePct": round(float((price - prev) / max(prev, 0.01) * 100), 2) if prev else 0,
            "prevClose": round(float(prev), 2) if prev else 0,
            "volume": info.get("volume", 0) or 0,
            "dayHigh": info.get("dayHigh", 0) or 0,
            "dayLow": info.get("dayLow", 0) or 0,
            "week52High": info.get("fiftyTwoWeekHigh", 0) or 0,
            "week52Low": info.get("fiftyTwoWeekLow", 0) or 0,
            "marketCap": info.get("marketCap", 0) or 0,
            "peRatio": info.get("trailingPE", 0) or 0,
            "source": "yahoo_finance",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.debug(f"Yahoo Finance failed for {symbol}: {e}")
        return None


# ─── Finnhub REST Fallback (US stocks only) ────────────────────

async def fetch_finnhub_quote(symbol: str, api_key: str, client: httpx.AsyncClient) -> Optional[dict]:
    """Fetch quote from Finnhub REST API (US stocks only, 60 calls/min)."""
    if not api_key:
        return None
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    try:
        await _rate_limiter.acquire("finnhub.io")
        resp = await client.get(
            f"https://finnhub.io/api/v1/quote?symbol={clean_symbol}&token={api_key}",
            timeout=10
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data.get("c"):
            return None
        return {
            "symbol": symbol,
            "price": round(float(data["c"]), 2),
            "change": round(float(data["d"] or 0), 2),
            "changePct": round(float(data["dp"] or 0), 2),
            "prevClose": round(float(data["pc"] or 0), 2),
            "dayHigh": round(float(data["h"] or 0), 2),
            "dayLow": round(float(data["l"] or 0), 2),
            "volume": 0,
            "week52High": 0,
            "week52Low": 0,
            "marketCap": 0,
            "peRatio": 0,
            "source": "finnhub",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.debug(f"Finnhub failed for {symbol}: {e}")
        return None


# ─── Batch Scraping Engine ─────────────────────────────────────

class MarketDataScraper:
    """
    Production-grade market data scraper with:
    - Async concurrent fetching
    - Auto-fallback chain (Google → Yahoo → Finnhub)
    - In-memory cache with TTL
    - Per-domain rate limiting
    - Anti-detection fingerprinting
    """

    def __init__(self, finnhub_key: str = "", cache_ttl: int = 30):
        self._finnhub_key = finnhub_key
        self._cache: dict[str, dict] = {}
        self._cache_ttl = cache_ttl
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            try:
                import ssl
                import certifi
                ssl_ctx = ssl.create_default_context(cafile=certifi.where())
                self._client = httpx.AsyncClient(
                    http2=True,
                    verify=ssl_ctx,
                    follow_redirects=True,
                    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
                    timeout=15,
                )
            except (ImportError, Exception) as e:
                logger.warning(f"SSL context creation failed ({e}), using default verification")
                self._client = httpx.AsyncClient(
                    http2=True,
                    verify=True,
                    follow_redirects=True,
                    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
                    timeout=15,
                )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _is_cached(self, symbol: str) -> bool:
        if symbol in self._cache:
            if time.time() - self._cache[symbol].get("timestamp", 0) < self._cache_ttl:
                return True
        return False

    async def get_quote(self, symbol: str) -> dict:
        """Get real-time quote with auto-fallback chain. Yahoo-first for reliability."""
        # Check cache
        if self._is_cached(symbol):
            return self._cache[symbol]

        client = await self._get_client()

        # Tier 1: Yahoo Finance (most reliable, runs non-blocking)
        try:
            quote = await asyncio.to_thread(fetch_yahoo_quote, symbol)
            if quote and quote.get("price", 0) > 0:
                self._cache[symbol] = quote
                logger.debug(f"Quote for {symbol} from Yahoo Finance")
                return quote
        except Exception as e:
            logger.debug(f"Yahoo Finance async call failed for {symbol}: {e}")

        # Tier 2: Google Finance scraping (fragile — may get 302 redirects)
        try:
            quote = await scrape_google_finance(symbol, client)
            if quote and quote.get("price", 0) > 0:
                self._cache[symbol] = quote
                logger.debug(f"Quote for {symbol} from Google Finance")
                return quote
        except Exception as e:
            logger.debug(f"Google Finance failed for {symbol}: {e}")

        # Tier 3: Finnhub (US stocks only)
        if not symbol.endswith((".NS", ".BO", ".L", ".DE", ".T", ".HK")):
            try:
                quote = await fetch_finnhub_quote(symbol, self._finnhub_key, client)
                if quote and quote.get("price", 0) > 0:
                    self._cache[symbol] = quote
                    logger.debug(f"Quote for {symbol} from Finnhub")
                    return quote
            except Exception as e:
                logger.debug(f"Finnhub failed for {symbol}: {e}")

        # Return empty quote
        return {
            "symbol": symbol, "price": 0, "change": 0, "changePct": 0,
            "prevClose": 0, "volume": 0, "dayHigh": 0, "dayLow": 0,
            "week52High": 0, "week52Low": 0, "marketCap": 0, "peRatio": 0,
            "source": "none", "timestamp": time.time(),
        }

    async def get_batch_quotes(self, symbols: list[str], concurrency: int = 8) -> list[dict]:
        """Batch fetch quotes with controlled concurrency."""
        semaphore = asyncio.Semaphore(concurrency)
        results = []

        async def _fetch(sym: str):
            async with semaphore:
                return await self.get_quote(sym)

        tasks = [_fetch(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, dict) else {"symbol": s, "price": 0, "source": "error"}
                for r, s in zip(results, symbols)]

    def clear_cache(self):
        self._cache.clear()

    def get_cache_stats(self) -> dict:
        now = time.time()
        valid = sum(1 for v in self._cache.values() if now - v.get("timestamp", 0) < self._cache_ttl)
        return {"total": len(self._cache), "valid": valid, "expired": len(self._cache) - valid}
