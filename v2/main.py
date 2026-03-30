"""
TradeOS V2 — FastAPI Gateway
REST + WebSocket API serving all platform intelligence.
Hides all internal methods/algorithms from client-facing output.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from v2.config.settings import settings
from v2.data.stock_universe import (
    STOCK_UNIVERSE, INDIAN_STOCKS, US_STOCKS, UK_STOCKS, EU_STOCKS, ASIA_STOCKS, ETF_INDICES,
    get_stock_info, get_sector_stocks, get_exchange_stocks, get_sectors, get_exchanges,
)
from v2.data.data_manager import data_manager
from v2.analytics.engine import (
    compute_full_analysis, compute_herding_csad, compute_piotroski_f_score,
)
from v2.models.regime_detector import get_regime_detector
from v2.models.signal_model import get_signal_model
from v2.models.volatility_model import volatility_forecaster
from v2.models.sentiment_engine import get_sentiment_engine
from v2.models.decision_synthesizer import decision_synthesizer
from v2.trading.paper_trading import get_or_create_portfolio

# Optional crawler
try:
    from v2.crawler.news_crawler import get_stock_news
    HAS_CRAWLER = True
except ImportError:
    HAS_CRAWLER = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("tradeos.api")


# ─── Security Middleware ──────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter per client IP."""
    def __init__(self, app, max_per_minute: int = 30):
        super().__init__(app)
        self._max = max_per_minute
        self._requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health and static
        if request.url.path in ("/api/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip not in self._requests:
            self._requests[client_ip] = []

        # Clean old timestamps
        self._requests[client_ip] = [t for t in self._requests[client_ip] if now - t < 60]

        if len(self._requests[client_ip]) >= self._max:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please wait before making more requests."},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


# ─── Input Validation ─────────────────────────────────────────

_SYMBOL_RE = re.compile(r'^[A-Za-z0-9._\-]{1,20}$')

def validate_symbol(symbol: str) -> str:
    """Validate and sanitize stock symbol input."""
    symbol = symbol.strip().upper()
    if not _SYMBOL_RE.match(symbol):
        raise HTTPException(status_code=400, detail=f"Invalid symbol format: {symbol}")
    return symbol


def sanitize_numpy(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_numpy(v) for v in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Timestamp, pd.Timestamp)):
        return obj.isoformat()
    elif pd.isna(obj) if isinstance(obj, float) else False:
        return 0
    return obj


# ─── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    for w in settings.validate():
        logger.warning(w)
    yield
    logger.info("Shutting down...")
    await data_manager.cleanup()


# ─── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="TradeOS Intelligence Platform",
    version="2.0.0",
    description="Institutional-grade stock intelligence with 40+ indicators, 5-model AI pipeline, and paper trading.",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# ─── Request Models ───────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    symbol: str
    periodDays: int = 365

    @field_validator('symbol')
    @classmethod
    def clean_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not _SYMBOL_RE.match(v):
            raise ValueError(f'Invalid symbol: {v}')
        return v


class DecisionRequest(BaseModel):
    symbol: str


class PaperCreateRequest(BaseModel):
    initialBalance: float = 100000
    portfolioId: Optional[str] = None


class PaperTradeRequest(BaseModel):
    portfolioId: str
    symbol: str
    action: str = "BUY"
    positionSizePct: float = 3.0


class PaperCloseRequest(BaseModel):
    portfolioId: str
    positionId: str


class ChatRequest(BaseModel):
    messages: list[dict]
    context: str = ""
    symbol: Optional[str] = None


# ─── Health ────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    warnings = settings.validate()
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "platform": settings.APP_NAME,
        "apis": {
            "groq": bool(settings.GROQ_API_KEY),
            "finnhub": bool(settings.FINNHUB_API_KEY),
            "alphaVantage": bool(settings.ALPHA_VANTAGE_API_KEY),
            "fmp": bool(settings.FMP_API_KEY),
        },
        "warnings": warnings,
    }


# ─── Stocks ────────────────────────────────────────────────────

@app.get("/api/stocks")
async def list_stocks(exchange: Optional[str] = None, sector: Optional[str] = None):
    stocks = STOCK_UNIVERSE
    if exchange:
        stocks = [s for s in stocks if s["exchange"] == exchange]
    if sector:
        stocks = [s for s in stocks if s["sector"] == sector]
    return {
        "stocks": stocks,
        "total": len(stocks),
        "exchanges": get_exchanges(),
        "sectors": get_sectors(),
    }


@app.get("/api/stocks/markets")
async def market_summary():
    return {
        "indian": {"count": len(INDIAN_STOCKS), "exchange": "NSE"},
        "us": {"count": len(US_STOCKS), "exchanges": ["NYSE", "NASDAQ"]},
        "uk": {"count": len(UK_STOCKS), "exchange": "LSE"},
        "europe": {"count": len(EU_STOCKS), "exchange": "XETRA"},
        "asia": {"count": len(ASIA_STOCKS), "exchanges": ["TSE", "HKEX"]},
        "etfs": {"count": len(ETF_INDICES)},
        "total": len(STOCK_UNIVERSE),
    }


# ─── Real-Time Quote ──────────────────────────────────────────

@app.get("/api/quote/{symbol}")
async def get_quote(symbol: str):
    quote = await data_manager.get_quote(symbol)
    if not quote or quote.get("price", 0) == 0:
        raise HTTPException(status_code=404, detail=f"Quote not found for {symbol}")
    # Remove internal fields
    quote.pop("source", None)
    quote.pop("timestamp", None)
    return quote


@app.get("/api/quotes/batch")
async def batch_quotes(symbols: str = Query(..., description="Comma-separated symbols")):
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()][:20]
    quotes = await data_manager.get_batch_quotes(symbol_list)
    for q in quotes:
        q.pop("source", None)
        q.pop("timestamp", None)
    return {"quotes": quotes}


# ─── Price Chart ────────────────────────────────────────────────

@app.get("/api/chart/{symbol}")
async def get_chart(symbol: str, period: int = 365, interval: str = "1d"):
    df = data_manager.get_historical(symbol, period, interval)
    if df.empty:
        raise HTTPException(status_code=404, detail="No historical data available")

    # Sample to ~200 points for charting
    step = max(1, len(df) // 200)
    sampled = df.iloc[::step]

    chart_data = [
        {
            "date": d.strftime("%Y-%m-%d %H:%M") if interval != "1d" else d.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        }
        for d, row in sampled.iterrows()
    ]
    return {"symbol": symbol, "interval": interval, "data": chart_data}


# ─── Full Analysis ──────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """Full analysis: 40+ indicators + regime + signals + sentiment + decision."""
    symbol = req.symbol

    # Fetch data
    df = data_manager.get_historical(symbol, req.periodDays)
    if df.empty or len(df) < 30:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")

    # Quote
    quote = await data_manager.get_quote(symbol)
    quote.pop("source", None)
    quote.pop("timestamp", None)

    # ── Fill null/zero quote fields from historical data ──
    if quote.get("dayHigh", 0) == 0 and not df.empty:
        quote["dayHigh"] = round(float(df["High"].iloc[-1]), 2)
    if quote.get("dayLow", 0) == 0 and not df.empty:
        quote["dayLow"] = round(float(df["Low"].iloc[-1]), 2)
    if quote.get("week52High", 0) == 0 and len(df) >= 20:
        quote["week52High"] = round(float(df["High"].max()), 2)
    if quote.get("week52Low", 0) == 0 and len(df) >= 20:
        quote["week52Low"] = round(float(df["Low"].min()), 2)
    if quote.get("volume", 0) == 0 and not df.empty:
        quote["volume"] = int(df["Volume"].iloc[-1])

    # Multi-timeframe data
    tf_data = data_manager.get_multi_timeframe(symbol)

    # Analytics engine — all 40+ indicators
    indicators = compute_full_analysis(df, tf_data)

    # Regime Detection
    regime_detector = get_regime_detector()
    regime = regime_detector.predict(df)

    # Signal Model (Indicator Consensus — pure math)
    signal_model = get_signal_model()
    signal = signal_model.predict(df, regime.get("regime", "LOW_VOL_RANGE"))

    # Volatility Forecast
    vol_forecast = volatility_forecaster.forecast(df)

    # Fundamentals
    fundamentals = await data_manager.get_fundamentals(symbol)
    f_score = compute_piotroski_f_score(fundamentals)

    # Sentiment + News Articles
    sentiment = {"score": 0, "label": "NEUTRAL", "articleCount": 0, "confidence": 0}
    sentiment_articles = []
    try:
        news = await data_manager.get_news(symbol)
        if news:
            sentiment_engine = get_sentiment_engine()
            sentiment = await sentiment_engine.analyze_articles(news, symbol)
            # Build article list with sources for transparency
            for article in news[:20]:  # Cap at 20 articles
                sentiment_articles.append({
                    "title": article.get("headline", article.get("title", "Untitled")),
                    "source": article.get("source", "Unknown"),
                    "url": article.get("url", ""),
                    "date": article.get("datetime", article.get("publishedDate", "")),
                    "summary": article.get("summary", "")[:200],
                })
    except Exception as e:
        logger.warning(f"Sentiment analysis failed: {e}")

    # Herding (if sector available)
    herding = {"herdingDetected": False, "intensity": 0}
    info = get_stock_info(symbol)
    if info:
        sector_returns = data_manager.get_sector_returns(info["sector"], req.periodDays)
        if not sector_returns.empty:
            herding = compute_herding_csad(sector_returns, regime.get("regime", "LOW_VOL_RANGE"))

    # Price chart data
    step = max(1, len(df) // 120)
    chart_data = [
        {"date": d.strftime("%Y-%m-%d"), "open": round(float(r["Open"]), 2),
         "high": round(float(r["High"]), 2), "low": round(float(r["Low"]), 2),
         "close": round(float(r["Close"]), 2), "volume": int(r["Volume"])}
        for d, r in df.iloc[::step].iterrows()
    ]

    # ── Clean output ──
    response = {
        "quote": quote,
        "chart": chart_data,
        "regime": {
            "current": regime.get("regime", "LOW_VOL_RANGE"),
            "confidence": regime.get("confidence", 0.5),
        },
        "signal": {
            "action": signal.get("action", "HOLD"),
            "confidence": signal.get("confidence", 0.5),
            "probabilities": signal.get("probabilities", {}),
            "method": signal.get("method", "indicator_consensus"),
            "consensusScore": signal.get("consensusScore", 0),
            "bullishIndicators": signal.get("bullishIndicators", 0),
            "bearishIndicators": signal.get("bearishIndicators", 0),
            "indicatorBreakdown": signal.get("indicatorBreakdown", {}),
        },
        "indicators": indicators,
        "sentiment": {
            "score": sentiment.get("score", 0),
            "label": sentiment.get("label", "NEUTRAL"),
            "articleCount": sentiment.get("articleCount", 0),
            "articles": sentiment_articles,
        },
        "volatility": {
            "forecasted": vol_forecast.get("forecastedVolAnnualized", 0),
            "historical": vol_forecast.get("historicalVolAnnualized", 0),
            "riskLevel": vol_forecast.get("riskLevel", "NORMAL"),
        },
        "fundamentals": {**fundamentals, "fScore": f_score},
        "herding": herding,
        "multiTimeframe": indicators.get("multiTimeframe", {}),
    }
    return sanitize_numpy(response)


# ─── AI Trading Decision ───────────────────────────────────────

@app.post("/api/decision/{symbol}")
async def get_decision(symbol: str):
    """Generate AI trading decision with entry/SL/TP/position size."""
    df = data_manager.get_historical(symbol, 365)
    if df.empty or len(df) < 30:
        raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")

    quote = await data_manager.get_quote(symbol)
    current_price = quote.get("price", 0)
    if current_price == 0:
        raise HTTPException(status_code=404, detail="Unable to fetch current price")

    tf_data = data_manager.get_multi_timeframe(symbol)
    indicators = compute_full_analysis(df, tf_data)

    regime = get_regime_detector().predict(df)
    signal = get_signal_model().predict(df, regime.get("regime", "LOW_VOL_RANGE"))
    vol_forecast = volatility_forecaster.forecast(df)
    fundamentals = await data_manager.get_fundamentals(symbol)
    f_score = compute_piotroski_f_score(fundamentals)

    sentiment = {"score": 0, "label": "NEUTRAL", "articleCount": 0}
    try:
        news = await data_manager.get_news(symbol)
        if news:
            sentiment = await get_sentiment_engine().analyze_articles(news, symbol)
    except Exception:
        pass

    mtf = indicators.get("multiTimeframe", {})

    decision = await decision_synthesizer.generate_decision(
        symbol=symbol,
        current_price=current_price,
        indicators=indicators,
        regime=regime,
        signal=signal,
        sentiment=sentiment,
        volatility=vol_forecast,
        fundamentals={**fundamentals, **f_score},
        multi_tf=mtf,
    )

    # Clean output — no internal method names
    decision.pop("signalBreakdown", {})
    info = get_stock_info(symbol)
    decision["name"] = info["name"] if info else symbol
    decision["currentPrice"] = current_price

    return sanitize_numpy(decision)


# ─── Sentiment ──────────────────────────────────────────────────

@app.get("/api/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    engine = get_sentiment_engine()
    cached = engine.get_cached_sentiment(symbol)
    if cached:
        return cached

    info = get_stock_info(symbol)
    company_name = info["name"] if info else symbol

    # Try Finnhub news first
    news = await data_manager.get_news(symbol)

    # If Finnhub has no news, try crawler
    if not news and HAS_CRAWLER:
        try:
            news = await get_stock_news(symbol, company_name, max_results=8)
        except Exception as e:
            logger.warning(f"News crawler failed: {e}")

    if not news:
        return {"score": 0, "label": "NEUTRAL", "articleCount": 0, "confidence": 0, "articles": []}

    sentiment = await engine.analyze_articles(news, symbol)
    return sentiment


# ─── Paper Trading ──────────────────────────────────────────────

@app.post("/api/paper/create")
async def create_portfolio(req: PaperCreateRequest):
    engine = get_or_create_portfolio(req.portfolioId, req.initialBalance)
    return engine.get_portfolio()


@app.get("/api/paper/portfolio/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    engine = get_or_create_portfolio(portfolio_id)
    return engine.get_portfolio()


@app.get("/api/paper/positions/{portfolio_id}")
async def get_positions(portfolio_id: str):
    engine = get_or_create_portfolio(portfolio_id)
    return {"positions": engine.get_positions()}


@app.post("/api/paper/trade")
async def execute_paper_trade(req: PaperTradeRequest):
    engine = get_or_create_portfolio(req.portfolioId)
    quote = await data_manager.get_quote(req.symbol)
    price = quote.get("price", 0)
    if price == 0:
        raise HTTPException(status_code=404, detail="Cannot fetch price")

    # Get AI decision for SL/TP levels
    df = data_manager.get_historical(req.symbol, 90)
    atr_pct = 0.02
    if not df.empty and len(df) > 14:
        from v2.analytics.engine import compute_atr
        atr_data = compute_atr(df)
        atr_pct = atr_data.get("atrPct", 2) / 100

    if req.action == "BUY":
        sl = round(price * (1 - 2 * atr_pct), 2)
        tp1 = round(price * (1 + 2 * atr_pct), 2)
        tp2 = round(price * (1 + 4 * atr_pct), 2)
    else:
        sl = round(price * (1 + 2 * atr_pct), 2)
        tp1 = round(price * (1 - 2 * atr_pct), 2)
        tp2 = round(price * (1 - 4 * atr_pct), 2)

    result = engine.open_position(
        symbol=req.symbol,
        action=req.action,
        price=price,
        position_size_pct=req.positionSizePct,
        stop_loss=sl,
        take_profit_1=tp1,
        take_profit_2=tp2,
    )
    engine.save()
    return result


@app.post("/api/paper/close")
async def close_paper_trade(req: PaperCloseRequest):
    engine = get_or_create_portfolio(req.portfolioId)
    pos = engine.positions.get(req.positionId)
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")

    quote = await data_manager.get_quote(pos.symbol)
    price = quote.get("price", pos.current_price)
    result = engine.close_position(req.positionId, price, "MANUAL")
    engine.save()
    return result


@app.get("/api/paper/history/{portfolio_id}")
async def get_trade_history(portfolio_id: str):
    engine = get_or_create_portfolio(portfolio_id)
    return {"trades": engine.get_trade_history()}


@app.get("/api/paper/performance/{portfolio_id}")
async def get_performance(portfolio_id: str):
    engine = get_or_create_portfolio(portfolio_id)
    return engine.get_performance()


# ─── AI Chat ───────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not settings.GROQ_API_KEY:
        return {"response": "⚠️ AI features require GROQ_API_KEY. Please configure it in .env"}

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)

        system = """You are **TradeOS AI**, an expert institutional quantitative analyst and trading advisor.

Your expertise spans:
- Technical analysis (40+ indicators across trend, momentum, volatility, volume)
- Market regime analysis (bull, bear, range, crisis detection)
- Behavioral finance (herding detection, panic scoring, behavior gap analysis)
- Position sizing and risk management (Kelly Criterion, ATR-based stops)
- Global markets (NSE, NYSE, LSE, XETRA, TSE, HKEX)

RULES:
1. Always use ₹ for Indian stocks, $ for US stocks, £ for UK stocks, etc.
2. Provide specific, actionable insights — not vague advice
3. When discussing signals, describe them in trader-friendly terms (not algorithm names)
4. Never mention internal model names (XGBoost, GARCH, HMM) — describe their output in plain language
5. If asked about non-finance topics, politely redirect to market topics
6. Keep responses concise with clear formatting
7. When discussing risk, always mention position sizing and stop-loss importance"""

        if req.context:
            system += f"\n\nCurrent analysis context:\n{req.context}"

        if req.symbol:
            quote = await data_manager.get_quote(req.symbol)
            if quote.get("price", 0) > 0:
                system += f"\n\nCurrent data for {req.symbol}: Price=₹{quote['price']}, Change={quote.get('changePct', 0)}%"

        messages = [{"role": "system", "content": system}] + req.messages
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return {"response": response.choices[0].message.content}

    except Exception as e:
        return {"response": f"⚠️ Error: {str(e)}"}


# ─── Market Status ──────────────────────────────────────────────

@app.get("/api/market/status")
async def market_status():
    exchanges = ["NSE", "NYSE", "NASDAQ", "LSE", "XETRA", "TSE", "HKEX"]
    statuses = {}
    for ex in exchanges:
        statuses[ex] = data_manager.get_market_status(ex)
    return {"markets": statuses}


# ─── Top Movers ─────────────────────────────────────────────────

@app.get("/api/movers")
async def top_movers(exchange: str = "NSE", limit: int = 10):
    from v2.data.stock_universe import get_exchange_stocks
    stocks = get_exchange_stocks(exchange)
    symbols = [s["symbol"] for s in stocks[:30]]  # Limit to 30 for speed

    quotes = await data_manager.get_batch_quotes(symbols, concurrency=5)
    valid = [q for q in quotes if q.get("price", 0) > 0]

    # Sort by absolute change %
    valid.sort(key=lambda q: abs(q.get("changePct", 0)), reverse=True)

    gainers = [q for q in valid if q.get("changePct", 0) > 0][:limit]
    losers = [q for q in valid if q.get("changePct", 0) < 0][:limit]

    for q in gainers + losers:
        q.pop("source", None)
        q.pop("timestamp", None)

    return {"gainers": gainers, "losers": losers, "exchange": exchange}


# ─── WebSocket — Live Data Stream ───────────────────────────────

@app.websocket("/ws/live/{symbol}")
async def live_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()
    try:
        while True:
            quote = await data_manager.get_quote(symbol)
            quote.pop("source", None)
            quote.pop("timestamp", None)
            await websocket.send_json({"type": "quote", "data": quote})
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


# ─── Global Error Handler ───────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return safe error responses."""
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ─── Run ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    for w in settings.validate():
        logger.warning(w)
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
