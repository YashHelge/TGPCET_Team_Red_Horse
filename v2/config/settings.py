"""
TradeOS V2 — Centralized Configuration
All API keys, rate limits, market hours, and analytics thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)


class Settings:
    """Production-grade application configuration."""

    # ── API Keys ────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VINTAGE_API_KEY", "")
    TWELVE_DATA_API_KEY: str = os.getenv("TWELVE_DATA_API_KEY", "")
    FMP_API_KEY: str = os.getenv("FINANCIAL_MODELING_PREP", "")

    # ── Rate Limits (requests per window) ───────────────────────
    FINNHUB_RATE_LIMIT: int = 60          # 60 calls/min
    ALPHA_VANTAGE_RATE_LIMIT: int = 25    # 25 calls/day
    FMP_RATE_LIMIT: int = 250             # 250 calls/day
    TWELVE_DATA_RATE_LIMIT: int = 8       # 8 calls/min
    GROQ_RATE_LIMIT: int = 30             # 30 calls/min (free tier)
    SCRAPER_RATE_LIMIT: int = 20          # 20 calls/min per domain

    # ── Cache TTLs (seconds) ────────────────────────────────────
    CACHE_TTL_REALTIME: int = 30          # 30s for live quotes
    CACHE_TTL_INDICATORS: int = 300       # 5 min for computed indicators
    CACHE_TTL_HISTORICAL: int = 3600      # 1 hour for OHLCV history
    CACHE_TTL_FUNDAMENTALS: int = 86400   # 24 hours for fundamentals
    CACHE_TTL_NEWS: int = 600             # 10 min for news
    CACHE_TTL_SENTIMENT: int = 900        # 15 min for sentiment scores

    # ── Analytics Thresholds ────────────────────────────────────
    HERDING_SIGNIFICANCE: float = 0.05    # p-value for herding detection
    PANIC_VOLUME_ZSCORE: float = 2.0      # Z-score threshold
    ADX_TREND_THRESHOLD: float = 25.0     # ADX > 25 = strong trend
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0
    CONFLUENCE_MIN_SIGNALS: int = 4       # 4/6 categories required

    # ── Position Sizing ─────────────────────────────────────────
    MAX_POSITION_PCT: float = 5.0         # Max 5% per trade
    MAX_SECTOR_EXPOSURE: float = 25.0     # Max 25% per sector
    CRISIS_MAX_POSITION: float = 2.0      # 2% in HIGH_VOL_CRISIS
    KELLY_FRACTION: float = 0.5           # Half-Kelly
    DEFAULT_SLIPPAGE: float = 0.0005      # 0.05% slippage

    # ── Paper Trading ───────────────────────────────────────────
    DEFAULT_VIRTUAL_BALANCE: float = 100000.0   # ₹1L
    TIME_STOP_DAYS: int = 5               # Exit if no progress in 5 days
    PANIC_EXIT_THRESHOLD: float = 65.0    # Panic > 65 → defensive exit
    SENTIMENT_REVERSAL_THRESHOLD: float = 0.4

    # ── Market Hours (IST) ──────────────────────────────────────
    MARKET_HOURS = {
        "NSE": {"open": "09:15", "close": "15:30", "tz": "Asia/Kolkata"},
        "BSE": {"open": "09:15", "close": "15:30", "tz": "Asia/Kolkata"},
        "NYSE": {"open": "09:30", "close": "16:00", "tz": "America/New_York"},
        "NASDAQ": {"open": "09:30", "close": "16:00", "tz": "America/New_York"},
        "LSE": {"open": "08:00", "close": "16:30", "tz": "Europe/London"},
        "TSE": {"open": "09:00", "close": "15:00", "tz": "Asia/Tokyo"},
        "HKEX": {"open": "09:30", "close": "16:00", "tz": "Asia/Hong_Kong"},
        "XETRA": {"open": "09:00", "close": "17:30", "tz": "Europe/Berlin"},
    }

    # ── Scraping Config ─────────────────────────────────────────
    SCRAPE_CONCURRENCY: int = 5
    SCRAPE_TIMEOUT: int = 15              # seconds
    SCRAPE_MIN_DELAY: float = 0.3         # min delay between requests
    SCRAPE_MAX_DELAY: float = 1.5         # max delay between requests

    # ── Security ─────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALLOWED_ORIGINS: list[str] = [
        o.strip() for o in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"
        ).split(",") if o.strip()
    ]
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    # ── App ──────────────────────────────────────────────────────
    APP_NAME: str = "TradeOS"
    APP_VERSION: str = "2.0.0"
    APP_TAGLINE: str = "Institutional-Grade Stock Intelligence Platform"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Storage ──────────────────────────────────────────────────
    DATA_DIR: Path = Path(__file__).resolve().parents[1] / "storage"
    MODELS_DIR: Path = Path(__file__).resolve().parents[1] / "storage" / "models"
    CACHE_DIR: Path = Path(__file__).resolve().parents[1] / "storage" / "cache"

    @classmethod
    def init_dirs(cls):
        """Create storage directories."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> list[str]:
        warnings = []
        if not cls.GROQ_API_KEY:
            warnings.append("GROQ_API_KEY not set — AI features disabled")
        if not cls.FINNHUB_API_KEY:
            warnings.append("FINNHUB_API_KEY not set — using scraping only")
        if not cls.ALPHA_VANTAGE_API_KEY:
            warnings.append("ALPHA_VANTAGE_API_KEY not set — fundamentals limited")
        if not cls.FMP_API_KEY:
            warnings.append("FMP_API_KEY not set — Piotroski F-Score unavailable")
        return warnings


settings = Settings()
settings.init_dirs()
