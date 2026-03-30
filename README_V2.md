# TradeOS Intelligence Platform

> **Architecture Blueprint v2.0** — A complete rebuild of the SheepOrSleep behavioral analytics engine into a production-grade, globally-scalable quantitative intelligence platform with real-time data, multi-model AI, autonomous paper trading simulation, and institutional-grade decision logic.

---

## Platform Stats

| Metric | Value |
|--------|-------|
| Analytics Parameters | 40+ |
| Specialized AI Models | 5 |
| Global Exchanges | 100+ |
| Real-Time Latency | < 150ms |
| Data API Cost | Free Tier |

---

## Table of Contents

1. [Core Philosophy](#1-core-philosophy)
2. [System Architecture](#2-system-architecture)
3. [Free Data APIs](#3-free-data-apis)
4. [Data Pipeline Design](#4-data-pipeline-design)
5. [Analytics Engine (40+ Parameters)](#5-analytics-engine)
6. [Multi-Model AI Pipeline](#6-multi-model-ai-pipeline)
7. [Decision Engine](#7-decision-engine)
8. [Paper Trading Simulation](#8-paper-trading-simulation)
9. [Global Markets](#9-global-markets)
10. [Tech Stack](#10-tech-stack)
11. [Microservices Map](#11-microservices-map)
12. [Build Roadmap](#12-build-roadmap)

---

## 1. Core Philosophy

### Why the original system fails — and how we fix it

The original **SheepOrSleep** was architecturally sound but analytically narrow. A single LLM call, 5 panic parameters, and batch yfinance data cannot make reliable trading decisions.

#### ❌ Old System — What Was Wrong

- Batch yfinance polling — no real-time tick data
- 5 panic indicators only — ignores 95% of market signals
- CCK OLS is a *detection* model, not a *prediction* model
- Single LLaMA call with no signal validation — hallucination-prone
- No position sizing logic — "buy" without "how much"
- India-only, no global market support
- Monte Carlo simulation used wrong — backward-looking only
- No market regime detection — same strategy in all conditions

#### ✅ New System — The TradeOS Approach

- Finnhub WebSocket — sub-150ms real-time tick feed
- 40+ indicators across 8 orthogonal signal categories
- HMM regime classifier + XGBoost signal model
- 5-model AI ensemble — each specialized, outputs validated
- Kelly Criterion + ATR-based stop/target — every decision quantified
- 100+ exchanges — NSE, NYSE, LSE, TSE, HKEX, and more
- Forward-looking Monte Carlo with live regime bias
- HMM detects trending/ranging/crisis — adaptive strategy per regime

> **The Trader's Mindset:** A professional trader never makes a decision based on a single signal. They synthesize trend, momentum, volume, volatility, sentiment, fundamentals, and market regime simultaneously. TradeOS replicates this multi-dimensional thinking algorithmically — signals must *converge* before a decision is generated, and every decision comes with a precise entry price, stop loss, take profit, and position size.

---

## 2. System Architecture

Production-grade, event-driven architecture built around Apache Kafka as the central event bus, with TimescaleDB for time-series persistence and Redis for sub-millisecond caching.

```
DATA SOURCES
  Finnhub (WS)  ·  Alpha Vantage  ·  yfinance  ·  FMP  ·  News RSS
                             ↓
                       Apache Kafka
           (market.ticks · analytics.signals · ai.decisions · alerts)
                    ↙           ↓            ↘
          Flink/Celery        Redis         Celery Beat
         Stream Processing   Hot Cache      Batch Jobs
                    ↘           ↓            ↙
    ┌──────────────────────────────────────────────────┐
    │  Regime    Signal    Sentiment   Volatility  LLaMA│
    │  HMM      XGBoost   FinBERT    GARCH(1,1)  3.3 70B│
    └──────────────────────────────────────────────────┘
                             ↓
               FastAPI Gateway + WebSocket Server
          ↙        ↙         ↓          ↘         ↘
      Next.js   Flutter   Paper Trade  Streamlit  Alerts
      Web UI    Mobile    Simulator    Research   TG/Email

STORAGE (side-channel)
  TimescaleDB (OHLCV time-series)  ·  ClickHouse (OLAP analytics)
```

### Key Architectural Principles

**Event-Driven Core** — Every price tick flows through Kafka as an immutable event. Services subscribe to specific topics — decoupled, horizontally scalable, and replay-able for backtesting.

**Sub-150ms Decision Loop** — Finnhub WebSocket → Kafka → Flink (TA compute) → Redis pub/sub → FastAPI WebSocket push to client. The complete cycle completes in under 150ms end-to-end.

**AI as a Service Layer** — ML models run asynchronously and publish outputs back to Kafka. The LLaMA synthesizer consumes all model outputs, never raw market data — grounding it in vetted signals.

---

## 3. Free Data APIs

Global real-time data with zero cost. Three complementary APIs cover real-time ticks, fundamentals, and historical data — all on their free tiers.

| Provider | Free Tier | WebSocket | Latency | Coverage | Role in TradeOS |
|----------|-----------|-----------|---------|----------|-----------------|
| **Finnhub** `finnhub.io` | 60 calls/min + WS unlimited | ✅ Yes | < 100ms | 60+ exchanges (NSE, NYSE, LSE) | **PRIMARY · Live Feed** |
| **Alpha Vantage** `alphavantage.co` | 25 calls/day | ❌ REST | REST | 50+ markets | **SECONDARY · Indicators** |
| **yfinance** `pypi: yfinance` | Unlimited* (unofficial) | ❌ Batch | Batch | 100+ markets | **TERTIARY · Batch/History** |
| **Financial Modeling Prep** `financialmodelingprep.com` | 250 calls/day | ✅ Yes | < 50ms | Global stocks | **FUNDAMENTAL · Valuations** |
| **Twelve Data** `twelvedata.com` | 8 calls/min | ✅ Yes | ~170ms | 80 exchanges | **BACKUP · WS Fallback** |
| **Polygon.io** `polygon.io` | EOD free, RT paid | ✅ (paid) | < 10ms | US Markets | **US UPGRADE · Future tier** |

> **Free Tier Strategy:** Finnhub's free WebSocket provides unlimited real-time streaming for 50 simultaneous tickers. Rotate the watchlist every session to cover more instruments. Alpha Vantage's 25 daily calls are used for *daily EOD fundamental refresh* only. yfinance covers the 2+ year historical window needed for ML model training.

### Indian Market Specifics

**NSE Direct** — `nsepy` wraps NSE India's unofficial REST endpoint. For real-time NSE ticks, `jugaad-trader` provides unofficial WebSocket access. Finnhub symbol format: `RELIANCE.NS`. BSE: `500325.BSE`.

**Mutual Fund NAV** — AMFI provides a completely free public API for all Indian mutual fund NAV data, updated daily.

```
GET https://api.mfapi.in/mf/119598
# Returns: date, nav for all schemes
```

---

## 4. Data Pipeline Design

Three-zone ingestion architecture with appropriate processing per velocity zone.

| Zone | Latency | Description | Tech |
|------|---------|-------------|------|
| **Zone 1 — Hot Data** | < 200ms | Finnhub WS ticks → Kafka `market.ticks` → Redis hot cache → Real-time charts | WebSocket + Redis Streams |
| **Zone 2 — Warm Data** | < 60s | 1-min OHLCV aggregation → TA-Lib indicator compute → Signal publish to `analytics.signals` | Celery + TA-Lib |
| **Zone 3 — Cold Data** | Daily | EOD OHLCV → TimescaleDB → ML model feature recompute → Alpha Vantage fundamental refresh | Celery Beat + Scheduler |
| **Zone 4 — Sentiment** | Continuous | Finnhub news feed → FinBERT NLP → Sentiment score timeseries → Sentiment signal merge | FinBERT + NLP Worker |

### Real-Time Ingestion (Code)

```python
# Finnhub WebSocket real-time tick ingestion
import finnhub, websocket, json
from kafka import KafkaProducer
import redis

producer = KafkaProducer(bootstrap_servers='kafka:9092')
r = redis.Redis(host='redis', decode_responses=True)

def on_message(ws, message):
    data = json.loads(message)
    for tick in data.get('data', []):
        # Publish to Kafka for ML processing
        producer.send('market.ticks', json.dumps(tick).encode())
        # Cache latest tick in Redis (sub-1ms reads)
        r.hset(f"tick:{tick['s']}", mapping={'p': tick['p'], 'v': tick['v'], 't': tick['t']})
        # Real-time WebSocket broadcast to frontend clients
        r.publish(f"live:{tick['s']}", json.dumps(tick))

ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={FINNHUB_KEY}", on_message=on_message)
ws.on_open = lambda ws: [ws.send(json.dumps({'type':'subscribe','symbol':s})) for s in WATCHLIST]
```

---

## 5. Analytics Engine

### 40+ Parameters Across 8 Orthogonal Signal Categories

> **Key Principle:** No two indicators in the same category. Each category measures a fundamentally different market dimension — eliminating signal redundancy and ensuring every AI pipeline input carries unique information.

---

### Category 01 — Price Action
*Raw market structure and candlestick context*

| Parameter | Description |
|-----------|-------------|
| OHLCV | Open · High · Low · Close · Volume |
| Heikin-Ashi | Smoothed candles for trend clarity |
| Candlestick Patterns | Doji · Hammer · Engulfing · Shooting Star (TA-Lib) |
| Price Gaps | Gap-up / gap-down detection with % magnitude |
| Opening Range (ORB) | First 15-min high/low breakout |
| Pivot Points | Classic S1/S2/R1/R2 from prior day |

---

### Category 02 — Trend Detection
*Direction, strength, and stage of prevailing trend*

| Parameter | Description |
|-----------|-------------|
| EMA 9/21/50/200 | Multi-timeframe trend alignment |
| MACD (12,26,9) | Momentum + trend divergence signal |
| ADX (14) | Trend strength · > 25 = strong trend |
| Parabolic SAR | Trailing stop · Trend reversal trigger |
| Ichimoku Cloud | Tenkan/Kijun/Senkou/Chikou (9,26,52) |
| SuperTrend | ATR-based dynamic trend line (3×ATR) |
| Linear Regression | Price vs 50-bar regression slope |

---

### Category 03 — Momentum
*Speed and conviction of price movement*

| Parameter | Description |
|-----------|-------------|
| RSI (14) | Overbought (> 70) / Oversold (< 30) |
| Stochastic (14,3,3) | K/D crossovers · Short-term momentum |
| Williams %R (14) | Reversal detection at extremes |
| MFI (14) | Volume-weighted RSI (Money Flow Index) |
| ROC (12) | 12-bar Rate of Change momentum |
| CCI (20) | Commodity Channel Index · Mean deviation |

---

### Category 04 — Volatility
*Risk environment and price range expansion/contraction*

| Parameter | Description |
|-----------|-------------|
| Bollinger Bands (20,2σ) | Volatility envelope · Squeeze detection |
| ATR (14) | True Range · Stop-loss calibration base |
| Keltner Channels | EMA(20) ± 2×ATR volatility filter |
| BB %B + Width | Band position + expansion rate |
| Historical Vol (30d) | Annualized σ vs long-run mean |
| GARCH(1,1) Forecast | Next-period conditional variance forecast |

---

### Category 05 — Volume Analysis
*Institutional participation and conviction behind price moves*

| Parameter | Description |
|-----------|-------------|
| VWAP | Volume-Weighted Avg Price · Institutional benchmark |
| OBV | On-Balance Volume · Cumulative buy/sell pressure |
| A/D Line | Accumulation/Distribution · Smart money flow |
| CMF (20) | Chaikin Money Flow · Buying vs selling pressure |
| Relative Volume | Current vol vs 20-day SMA · Anomaly flag |
| NVI | Negative Volume Index · Smart money behavior |
| Volume Profile | POC · HVN/LVN levels (Point of Control) |

---

### Category 06 — Behavioral Finance (Upgraded CCK)
*Retained + improved from SheepOrSleep's original core*

**Upgrade: CCK Herding → Dynamic CSAD with Regime Conditioning**

The original CCK OLS is purely backward-looking. The upgraded version conditions the herding test on the current market regime, allowing regime-specific herding thresholds:

```
CSAD_t = α + γ₁|R_m,t| + γ₂(R_m,t²) + γ₃·D_crisis·R_m,t² + ε_t
```

`D_crisis = 1` during high-volatility regime (from HMM). γ₃ captures amplified herding in crisis conditions — more statistically robust than uniform thresholds.

| Parameter | Description |
|-----------|-------------|
| CCK CSAD (Upgraded) | Regime-conditioned herding detection |
| Panic Score (5-Factor) | Vol Z-score + Delivery proxy + PV divergence + Drawdown + Vol regime |
| Behavior Gap | Pearson correlation penalty on realized CAGR |
| Short Interest | Days-to-cover · Contrarian signal |
| Put/Call Ratio | Options market fear/greed gauge |

---

### Category 07 — Fundamentals
*Valuation and financial health (daily refresh from FMP + Alpha Vantage)*

| Parameter | Description |
|-----------|-------------|
| P/E · P/B · P/S | Valuation multiples vs sector median |
| EPS Growth (YoY/QoQ) | Earnings acceleration/deceleration |
| Revenue Growth | Top-line expansion (YoY) |
| Debt/Equity | Financial leverage risk |
| FCF Yield | Free Cash Flow / Market Cap |
| ROE / ROCE | Capital efficiency metrics |
| Piotroski F-Score | 9-point financial health composite (0–9) |

---

### Category 08 — Multi-Timeframe Confluence
*The most ignored but most important signal dimension*

Every signal above is computed across **three timeframes simultaneously**: 15-min (intraday), 1-hour (swing), and 1-day (position). A trade signal is only issued when at least 2 of 3 timeframes are aligned. This single rule eliminates the majority of false signals that plague single-timeframe systems.

| Timeframe | Purpose |
|-----------|---------|
| 15-MIN | Entry timing · Intraday signals |
| 1-HOUR | Swing structure · Momentum context |
| DAILY | Primary trend · Major levels |

---

## 6. Multi-Model AI Pipeline

Five specialized models, one synthesized decision. Each model is an expert in its domain. The LLaMA synthesizer sees structured JSON outputs from all four upstream models — never raw data.

---

### Model 1 — Regime Classifier (HMM)

Classifies the current market into one of four hidden states. This output gates the entire downstream pipeline — different indicator weights and position sizes apply in each regime.

```
States: BULL_TRENDING | BEAR_TRENDING | LOW_VOL_RANGE | HIGH_VOL_CRISIS
```

**Inputs:** Return series · GARCH vol · ATR ratio · ADX value · Volume ratio

**Library:** `hmmlearn.hmm.GaussianHMM(n_components=4)`

---

### Model 2 — Technical Signal Model (XGBoost + LightGBM Ensemble)

Gradient boosting models trained on 5 years of walk-forward data. XGBoost and LightGBM are averaged for ensemble diversity. Each model outputs three probabilities: P(BUY), P(SELL), P(HOLD).

> **Why not LSTM?** Tree models outperform LSTM on tabular technical indicator features. LSTM excels at sequential raw price prediction — a different problem. XGBoost is faster, more interpretable, and less prone to overfitting on structured data.

**Feature Engineering:**
- All 40+ indicators (normalized 0–1)
- Cross-indicator divergence flags
- Multi-timeframe alignment scores
- Regime label from Model 1 (one-hot)
- Lag features (t-1, t-2, t-5 indicator values)
- Day-of-week + time-of-day (session bias)

**Validation:** Walk-Forward · Purged K-Fold (no look-ahead)

---

### Model 3 — Sentiment Analyzer (FinBERT + News NLP)

FinBERT classifies news headlines and company announcements into *positive*, *negative*, or *neutral*. Scores aggregated into a 24-hour rolling sentiment window with recency decay:

```
Sentiment_t = Σ(score_i × e^(-λ·age_i)) / N
```

`λ = 0.1` (decay constant — older news weighted less)

**News Sources:** Finnhub news API · Alpha Vantage news · NSE/BSE announcements · RSS feeds

**Groq Integration:** For complex multi-paragraph analyst reports, Groq LLaMA pre-summarizes → FinBERT classifies the summary. Best of both: LLaMA's comprehension + FinBERT's calibrated sentiment scoring.

---

### Model 4 — Volatility Forecaster (GARCH(1,1) + EGARCH)

GARCH models the time-varying nature of volatility — accounting for "volatility clustering" in financial markets. Forecasted variance directly feeds position sizing.

```
σ²_t = ω + α·ε²_(t-1) + β·σ²_(t-1)

EGARCH: ln(σ²_t) = ω + α|z_(t-1)| + γz_(t-1) + β·ln(σ²_(t-1))
```

EGARCH captures the *leverage effect* — negative returns increase volatility more than positive returns of the same magnitude. Critical for Indian markets.

**Downstream Use:**
- **Position sizing:** Higher forecast vol → smaller position
- **Stop calibration:** Stop = 2× max(ATR, GARCH_vol)
- **Signal filtering:** Extreme vol → no new entries (crisis filter)
- **Sharpe optimization:** Risk-adjust targets dynamically

**Library:** `arch.arch_model(returns, vol='EGARCH')`

---

### Model 5 — Decision Synthesizer (Groq LLaMA 3.3 70B)

The LLaMA model receives a structured JSON payload containing all upstream model outputs — *not* raw market data. This is the critical architectural difference from the original system.

```python
# Structured prompt injection — LLaMA never sees raw OHLCV
CONTEXT = {
  "regime": "BULL_TRENDING",                          # From HMM
  "signal_probs": {"BUY": 0.78, "SELL": 0.11, "HOLD": 0.11},  # XGBoost
  "timeframe_alignment": {"15m": "BUY", "1h": "BUY", "1d": "HOLD"},
  "sentiment_score": 0.62,                            # FinBERT
  "forecasted_vol": 0.021,                            # GARCH annualized daily
  "herd_detected": False,
  "panic_score": 23,
  "key_levels": {"support": 2847, "resistance": 2920},
  "current_price": 2863,
  "fundamental_tier": "STRONG"                        # F-Score 7/9
}
```

> **System Prompt Persona:** "You are an institutional quantitative trader with 20 years of experience across Indian and global markets. You receive structured signals from 4 analytical models. Your job: (1) identify whether signals are converging or conflicting, (2) state ONE clear action — BUY / SELL / HOLD, (3) specify exact entry price, stop loss, and take profit using the provided key levels and volatility forecast, (4) explain your reasoning in 3 sentences. Refuse to make a decision if fewer than 3 of 5 signal categories align. Always account for regime context."

---

## 7. Decision Engine

Every TradeOS output includes 6 precise values: **Action · Entry Price · Stop Loss · Take Profit · Position Size · Confidence**. Never a vague "this stock looks good."

### Signal Confluence Framework

A BUY/SELL signal requires a minimum **4 of 6** signal categories agreeing. This eliminates 60–70% of false signals.

| Signal Category | Example Condition |
|----------------|-------------------|
| ✅ Trend | ADX > 25, EMA cross aligned |
| ✅ Momentum | RSI 45–65 and rising |
| ✅ Volume | Price above VWAP with rising OBV |
| ✅ Behavioral | No herd detected, panic score < 35 |
| ~ Sentiment | Score ≥ 0.4 (mildly positive) |
| ✅ Fundamental | Tier STRONG or AVERAGE |

**5/6 Aligned → STRONG BUY**

---

### Position Sizing — Kelly Criterion (Half-Kelly)

Full Kelly Criterion is theoretically optimal but too aggressive. Half-Kelly provides 75% of the return with significantly lower drawdown. GARCH volatility adjusts size dynamically.

```
f* = (p/b) - (q/a)
Position% = (f*/2) × (1 / GARCH_vol_ratio)
```

`p` = win probability (XGBoost) · `b` = avg win size · `q` = 1-p · `a` = avg loss size  
`GARCH_vol_ratio` = forecasted_vol / 30d_avg_vol

| Rule | Value |
|------|-------|
| Max position per trade | 5% of portfolio |
| Max sector exposure | 25% (diversification cap) |
| Crisis override | 2% max (if HMM = HIGH_VOL_CRISIS) |

---

### ATR-Based Entry · Stop Loss · Take Profit

| Level | Formula | Notes |
|-------|---------|-------|
| **Entry** | VWAP or nearest support − 0.25×ATR | Wait for pullback, never chase breakouts |
| **Stop Loss** | Entry − (2×ATR14), min(SL, nearest support − 0.5%) | Adapts to market volatility |
| **Take Profit 1** | Entry + (2×ATR) → 50% exit | Breakeven + safe |
| **Take Profit 2** | Nearest resistance → 50% exit | Trailing stop on remainder |

**Trailing Stop Logic:** Once TP1 is hit, stop moves to breakeven for the remaining 50%. For every additional ATR move in favor, the trailing stop advances by 0.75×ATR.

---

### Sample Decision Output

```json
{
  "symbol": "RELIANCE.NS",
  "action": "BUY",
  "confidence": 0.82,
  "regime": "BULL_TRENDING",
  "entry": { "price": 2863.00, "type": "LIMIT" },
  "stop_loss": 2821.50,
  "take_profit_1": 2904.50,
  "take_profit_2": 2940.00,
  "position_size_pct": 3.8,
  "risk_reward": 1.85,
  "reasoning": "5/6 signal categories aligned on BULL_TRENDING regime. RSI at 54 (rising, not overbought), price above VWAP with strong OBV accumulation. No herd behavior detected. Entry at VWAP retest for optimal risk/reward.",
  "signal_breakdown": {
    "trend": "BULL",
    "momentum": "RISING",
    "volume": "ACCUMULATION",
    "volatility": "LOW",
    "sentiment": "POSITIVE"
  },
  "alerts": ["Earnings in 8 days — consider reducing position size"]
}
```

---

## 8. Paper Trading Simulation

A live AI agent trading virtual money in real-time. The simulation connects to the same live Finnhub WebSocket feed, executes virtual orders at real-time market prices, and behaves identically to a live trading system — including slippage simulation and dynamic exits.

### Simulation Engine Flow

1. **User configures portfolio** — Virtual balance (₹1L default), risk tolerance, watchlist of 5–20 symbols
2. **Real-time signal monitoring** — Full analytics + AI pipeline runs on all watchlist symbols. Signals fire when confluence threshold is met.
3. **Virtual order execution** — Market orders filled at last traded price + slippage (0.05% default, 0.1% for illiquid). Limit orders queue at specified price.
4. **Autonomous position management** — Real-time stop loss monitoring, TP1/TP2 scale-out, trailing stop advancement, regime change → forced exit, panic score spike → defensive exit.
5. **Performance analytics** — Sharpe Ratio · Max Drawdown · Win Rate · Avg R/R · P&L curve vs NIFTY/S&P benchmark

### Auto-Exit Conditions

| Trigger | Action |
|---------|--------|
| **STOP LOSS HIT** | Price breaches ATR stop → immediate market exit |
| **TAKE PROFIT SEQUENCE** | TP1 hit → exit 50%, move stop to breakeven. TP2 hit → exit remainder |
| **REGIME FLIP** | HMM switches BULL→BEAR/CRISIS → exit all longs within 1 candle close |
| **PANIC SPIKE** | Panic score > 65 → defensive 70% exit, remaining 30% with tight stop |
| **TIME STOP** | Position open > 5 days with no target progress → exit (avoid dead money) |
| **SENTIMENT REVERSAL** | Sentiment drops 0.4+ in < 2 hours (news shock) → reassess immediately |

### Monte Carlo Forward Simulation (Improved)

The simulation runs forward-looking Monte Carlo with *regime-biased random walks*. In `BULL_TRENDING` regime, the drift parameter μ is set to the stock's realized α (excess return over beta-adjusted market). In `BEAR/CRISIS` regime, μ is negatively biased — giving regime-realistic simulations vs the original regime-agnostic random walk.

---

## 9. Global Markets

TradeOS works identically across all markets. Currency normalization and market-hours awareness are handled at the data ingestion layer.

| Market | Exchange | Symbol Format | Data Source | Trading Hours (IST) | Currency |
|--------|----------|---------------|-------------|---------------------|----------|
| 🇮🇳 India | NSE / BSE | `RELIANCE.NS` | Finnhub + nsepy | 09:15 – 15:30 | INR |
| 🇺🇸 USA | NYSE / NASDAQ | `AAPL`, `MSFT` | Finnhub (WS) | 19:00 – 01:30 | USD |
| 🇬🇧 UK | LSE | `BARC.L` | Finnhub + AV | 13:30 – 22:00 | GBP |
| 🇩🇪 Germany | XETRA / FSE | `BMW.DE` | Finnhub + AV | 13:30 – 22:00 | EUR |
| 🇯🇵 Japan | TSE (Tokyo) | `7203.T` | yfinance | 05:30 – 12:30 | JPY |
| 🇭🇰 Hong Kong | HKEX | `0700.HK` | yfinance + AV | 05:30 – 12:00 | HKD |
| 🇮🇳 MF (India) | AMFI | `Scheme ID: 119598` | api.mfapi.in | Daily NAV | INR |
| 🌐 ETFs | NYSE / NSE | `SPY`, `NIFTYBEES.NS` | Finnhub | Market-specific | Multi |

> **Market Hours Intelligence:** TradeOS tracks market status (open/closed/pre-market) for every exchange via Finnhub's market status endpoint. SGX Nifty futures serve as a reliable Indian market open predictor.

---

## 10. Tech Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| **Data Stream** | Apache Kafka | Central event bus. Immutable events, replay for backtesting, 1M+ msg/sec throughput |
| **Hot Cache + Pub/Sub** | Redis 7 + Redis Streams | Sub-1ms reads, Pub/Sub for WebSocket fan-out, Bloom filters for dedup |
| **Time-Series Storage** | TimescaleDB | PostgreSQL extension with automatic time-based partitioning + continuous aggregates |
| **Analytics Warehouse** | ClickHouse | Columnar OLAP — multi-year backtest and regime analysis queries in milliseconds |
| **Stream Processing** | Apache Flink / Celery | Flink for stateful stream processing (rolling indicators), Celery for scheduled batch jobs |
| **TA Computation** | TA-Lib + pandas-ta | TA-Lib is C-backed — 10–100x faster than pure Python implementations |
| **ML Models** | XGBoost + hmmlearn + arch | Signal classification, HMM regime detection, GARCH volatility forecasting |
| **AI Inference** | Groq Cloud (LLaMA 3.3 70B) | Sub-500ms inference, JSON mode for structured output |
| **API Layer** | FastAPI + WebSocket | Async, native WebSocket for real-time client push, Redis pub/sub bridge |
| **Web Frontend** | Next.js 16 + Recharts | TradingView Lightweight Charts for candlesticks, WebSocket for live P&L |
| **Mobile** | Flutter | Reuse existing FinSight Flutter codebase. Same FastAPI backend — new endpoints only |
| **Infrastructure** | Docker + Kubernetes | Each microservice containerized. K8s HPA on Kafka consumer lag. Start with Docker Compose |

---

## 11. Microservices Map

Eight independent services — one unified intelligence.

| Service | Responsibility | Kafka Topics | Tech |
|---------|---------------|--------------|------|
| **market-ingestion** | Manages all external API connections. Normalizes data to unified schema. | `market.ticks`, `market.ohlcv`, `market.news` | Python + websocket-client |
| **analytics-engine** | Consumes market.ticks. Computes all 40+ indicators. Manages multi-timeframe OHLCV aggregation. | IN: `market.ticks` → OUT: `analytics.features` | Python + TA-Lib + pandas |
| **regime-detector** | Runs HMM regime classification every minute. Persists regime state to Redis. | IN: `analytics.features` → OUT: `ml.regime` | Python + hmmlearn |
| **signal-model** | XGBoost + LightGBM inference. Outputs P(BUY/SELL/HOLD) per symbol. Integrates regime from Redis. | IN: `analytics.features` → OUT: `ml.signals` | Python + xgboost + lightgbm |
| **sentiment-service** | Processes news via FinBERT. Computes decayed sentiment score per symbol. | IN: `market.news` → OUT: `ml.sentiment` | Python + transformers + FinBERT |
| **decision-service** | Aggregates all ML outputs. Applies signal confluence rules. Calls Groq LLaMA. Publishes final decision. | IN: `ml.*` → OUT: `decisions.live`, `decisions.paper` | Python + Groq SDK |
| **paper-trade-engine** | Manages virtual portfolios. Real-time position monitoring. Executes auto-exits on SL/TP/Regime triggers. | IN: `market.ticks`, `decisions.paper` → OUT: `portfolio.updates` | Python + Redis + TimescaleDB |
| **gateway-api** | FastAPI REST + WebSocket. Auth (JWT). Rate limiting. Serves all clients (web, mobile, Streamlit). | Subscribes: `decisions.live`, `portfolio.updates`, `market.ticks` | FastAPI + uvicorn |

### Scaling Strategies

- **market-ingestion:** 1 instance per exchange cluster. Stateless — simple horizontal scale.
- **analytics-engine:** Scale on Kafka consumer lag. Each instance handles a symbol partition. TA-Lib is CPU-bound — add workers per CPU core.
- **regime-detector:** Low throughput — 1 instance per 100 symbols. Model loaded in memory.
- **signal-model:** XGBoost inference is CPU-fast. 1 worker per 50 symbols.
- **sentiment-service:** GPU preferred for FinBERT. CPU fallback with batch size 1.
- **decision-service:** Groq API is the bottleneck (rate limit). Queue with Celery. Priority: existing positions first.
- **paper-trade-engine:** 1 instance per 1,000 paper portfolios. Position state in Redis. Audit trail in TimescaleDB.
- **gateway-api:** Stateless — scale horizontally behind NGINX.

---

## 12. Build Roadmap

Designed to give a working, demonstrable system at the end of each phase — not just at the end of the whole roadmap.

### Phase 1 — Foundation (2–3 weeks)
**Real-time Data + Analytics Core**

- [ ] Finnhub WebSocket ingestion
- [ ] Kafka + Redis setup (Docker)
- [ ] TA-Lib all 40+ indicators
- [ ] TimescaleDB for persistence
- [ ] FastAPI with WebSocket
- [ ] Next.js live candlestick chart

**Deliverable:** Live streaming dashboard showing real-time OHLCV + all technical indicators for any global stock

---

### Phase 2 — Intelligence (2–3 weeks)
**ML Models + Signal Pipeline**

- [ ] HMM Regime Classifier training
- [ ] XGBoost Signal Model (walk-forward)
- [ ] GARCH volatility forecaster
- [ ] FinBERT sentiment pipeline
- [ ] Signal confluence framework
- [ ] Upgraded CCK herding detection

**Deliverable:** System generates BUY/SELL/HOLD signals with confluence breakdown for any stock

---

### Phase 3 — Decision Engine (2 weeks)
**Groq Synthesis + Paper Trading**

- [ ] Groq LLaMA decision synthesizer
- [ ] Kelly Criterion position sizing
- [ ] ATR-based entry/stop/target
- [ ] Paper trading engine
- [ ] Auto-exit logic (all 6 conditions)
- [ ] Portfolio P&L dashboard

**Deliverable:** Complete autonomous paper trading agent — invest virtual ₹1L, watch it trade in real-time with full reasoning

---

### Phase 4 — Production (2 weeks)
**Global Markets + Kubernetes + Monitoring**

- [ ] Multi-exchange support (NSE/NYSE/LSE)
- [ ] Mutual fund NAV integration (AMFI)
- [ ] Kubernetes deployment configs
- [ ] Prometheus + Grafana monitoring
- [ ] Telegram alert integration
- [ ] Flutter mobile client

**Deliverable:** Production-ready, globally-scalable platform with monitoring, alerting, and mobile access

---

## ⚠️ The Golden Rule — Never Skip

Run every ML model through *purged, walk-forward cross-validation* before deployment. Standard k-fold leaks future information into training (the train/test boundary bleeds through time). Purged k-fold enforces a strict time-gap between train and test.

> A model that passes standard CV but fails purged CV was overfit to look-ahead bias — it will fail in production.

Use the `mlfinlab` library's `PurgedKFold` class.

---

## Contributing

This project is built by **Kritish Bokde**. Redesigned from the original SheepOrSleep system.

---

*TradeOS Intelligence Platform · Architecture Blueprint v2.0 · Production Grade*