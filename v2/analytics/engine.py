"""
TradeOS V2 — Analytics Engine
Computes all 40+ technical indicators across 8 categories.
Pure numpy/pandas implementation — no TA-Lib dependency required.
"""

import numpy as np
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger("tradeos.analytics")


# ═══════════════════════════════════════════════════════════════
# CATEGORY 01 — PRICE ACTION
# ═══════════════════════════════════════════════════════════════

def compute_heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Heikin-Ashi candles for trend clarity."""
    ha = pd.DataFrame(index=df.index)
    ha["HA_Close"] = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
    ha["HA_Open"] = 0.0
    ha.iloc[0, ha.columns.get_loc("HA_Open")] = (df["Open"].iloc[0] + df["Close"].iloc[0]) / 2
    for i in range(1, len(ha)):
        ha.iloc[i, ha.columns.get_loc("HA_Open")] = (ha["HA_Open"].iloc[i - 1] + ha["HA_Close"].iloc[i - 1]) / 2
    ha["HA_High"] = pd.concat([df["High"], ha["HA_Open"], ha["HA_Close"]], axis=1).max(axis=1)
    ha["HA_Low"] = pd.concat([df["Low"], ha["HA_Open"], ha["HA_Close"]], axis=1).min(axis=1)
    return ha


def detect_candlestick_patterns(df: pd.DataFrame) -> dict:
    """Detect key candlestick patterns."""
    if len(df) < 3:
        return {"patterns": []}

    o, h, l, c = df["Open"].iloc[-1], df["High"].iloc[-1], df["Low"].iloc[-1], df["Close"].iloc[-1]
    body = abs(c - o)
    full_range = h - l
    upper_shadow = h - max(o, c)
    lower_shadow = min(o, c) - l

    patterns = []

    # Doji
    if full_range > 0 and body / full_range < 0.1:
        patterns.append({"name": "Doji", "type": "neutral", "strength": 0.6})

    # Hammer (bullish)
    if full_range > 0 and lower_shadow > body * 2 and upper_shadow < body * 0.3:
        patterns.append({"name": "Hammer", "type": "bullish", "strength": 0.7})

    # Shooting Star (bearish)
    if full_range > 0 and upper_shadow > body * 2 and lower_shadow < body * 0.3:
        patterns.append({"name": "Shooting Star", "type": "bearish", "strength": 0.7})

    # Engulfing
    if len(df) >= 2:
        prev_o, prev_c = df["Open"].iloc[-2], df["Close"].iloc[-2]
        if c > o and prev_c < prev_o and c > prev_o and o < prev_c:
            patterns.append({"name": "Bullish Engulfing", "type": "bullish", "strength": 0.8})
        elif c < o and prev_c > prev_o and c < prev_o and o > prev_c:
            patterns.append({"name": "Bearish Engulfing", "type": "bearish", "strength": 0.8})

    # Morning/Evening Star
    if len(df) >= 3:
        o2, c2 = df["Open"].iloc[-3], df["Close"].iloc[-3]
        o1, c1 = df["Open"].iloc[-2], df["Close"].iloc[-2]
        body2 = abs(c2 - o2)
        body1 = abs(c1 - o1)
        if c2 < o2 and body1 < body2 * 0.3 and c > o and c > (o2 + c2) / 2:
            patterns.append({"name": "Morning Star", "type": "bullish", "strength": 0.85})
        elif c2 > o2 and body1 < body2 * 0.3 and c < o and c < (o2 + c2) / 2:
            patterns.append({"name": "Evening Star", "type": "bearish", "strength": 0.85})

    return {"patterns": patterns}


def detect_price_gaps(df: pd.DataFrame) -> dict:
    """Detect gap-up and gap-down patterns."""
    if len(df) < 2:
        return {"gap": None, "magnitude": 0}
    prev_close = df["Close"].iloc[-2]
    curr_open = df["Open"].iloc[-1]
    gap_pct = ((curr_open - prev_close) / prev_close) * 100

    if gap_pct > 0.5:
        return {"gap": "GAP_UP", "magnitude": round(gap_pct, 2)}
    elif gap_pct < -0.5:
        return {"gap": "GAP_DOWN", "magnitude": round(gap_pct, 2)}
    return {"gap": None, "magnitude": round(gap_pct, 2)}


def compute_pivot_points(df: pd.DataFrame) -> dict:
    """Compute classic pivot points from prior day."""
    if len(df) < 2:
        return {}
    h, l, c = df["High"].iloc[-2], df["Low"].iloc[-2], df["Close"].iloc[-2]
    pivot = (h + l + c) / 3
    return {
        "pivot": round(pivot, 2),
        "r1": round(2 * pivot - l, 2),
        "r2": round(pivot + (h - l), 2),
        "s1": round(2 * pivot - h, 2),
        "s2": round(pivot - (h - l), 2),
    }


def compute_opening_range(df_intraday: pd.DataFrame, minutes: int = 15) -> dict:
    """Compute Opening Range Breakout levels from intraday data."""
    if df_intraday.empty or len(df_intraday) < minutes:
        return {"orb_high": 0, "orb_low": 0}
    first_n = df_intraday.head(minutes)
    return {
        "orb_high": round(float(first_n["High"].max()), 2),
        "orb_low": round(float(first_n["Low"].min()), 2),
    }


# ═══════════════════════════════════════════════════════════════
# CATEGORY 02 — TREND DETECTION
# ═══════════════════════════════════════════════════════════════

def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_multi_ema(df: pd.DataFrame) -> dict:
    """EMA 9/21/50/200 trend alignment."""
    close = df["Close"]
    ema9 = compute_ema(close, 9)
    ema21 = compute_ema(close, 21)
    ema50 = compute_ema(close, 50)
    ema200 = compute_ema(close, 200) if len(close) >= 200 else pd.Series(dtype=float)

    # Trend alignment signal
    latest = close.iloc[-1]
    trend = "NEUTRAL"
    if not ema200.empty:
        if latest > ema9.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]:
            trend = "STRONG_BULL"
        elif latest < ema9.iloc[-1] < ema21.iloc[-1] < ema50.iloc[-1]:
            trend = "STRONG_BEAR"
        elif latest > ema50.iloc[-1]:
            trend = "BULL"
        elif latest < ema50.iloc[-1]:
            trend = "BEAR"

    return {
        "ema9": round(float(ema9.iloc[-1]), 2),
        "ema21": round(float(ema21.iloc[-1]), 2),
        "ema50": round(float(ema50.iloc[-1]), 2),
        "ema200": round(float(ema200.iloc[-1]), 2) if not ema200.empty else 0,
        "trend": trend,
    }


def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD indicator."""
    close = df["Close"]
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return {
        "macd": round(float(macd_line.iloc[-1]), 4),
        "signal": round(float(signal_line.iloc[-1]), 4),
        "histogram": round(float(histogram.iloc[-1]), 4),
        "crossover": "BULLISH" if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2] else
                     "BEARISH" if macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2] else "NONE",
    }


def compute_adx(df: pd.DataFrame, period: int = 14) -> dict:
    """Average Directional Index — trend strength."""
    high, low, close = df["High"], df["Low"], df["Close"]
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    plus_dm = np.where((high - high.shift(1)) > (low.shift(1) - low), np.maximum(high - high.shift(1), 0), 0)
    minus_dm = np.where((low.shift(1) - low) > (high - high.shift(1)), np.maximum(low.shift(1) - low, 0), 0)

    atr = pd.Series(tr).rolling(period).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / atr.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / atr.replace(0, np.nan)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(period).mean()

    return {
        "adx": round(float(adx.iloc[-1]), 2) if not np.isnan(adx.iloc[-1]) else 0,
        "plusDI": round(float(plus_di.iloc[-1]), 2) if not np.isnan(plus_di.iloc[-1]) else 0,
        "minusDI": round(float(minus_di.iloc[-1]), 2) if not np.isnan(minus_di.iloc[-1]) else 0,
        "trendStrength": "STRONG" if adx.iloc[-1] > 25 else "WEAK" if adx.iloc[-1] > 15 else "NONE",
    }


def compute_parabolic_sar(df: pd.DataFrame, af_start: float = 0.02, af_max: float = 0.2) -> dict:
    """Parabolic SAR for trend reversal detection."""
    high, low, close = df["High"].values, df["Low"].values, df["Close"].values
    n = len(high)
    sar = np.zeros(n)
    ep = np.zeros(n)
    af = np.full(n, af_start)
    trend = np.ones(n)

    sar[0] = low[0]
    ep[0] = high[0]

    for i in range(1, n):
        sar[i] = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])
        if trend[i - 1] == 1:  # Uptrend
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = ep[i - 1]
                ep[i] = low[i]
                af[i] = af_start
            else:
                trend[i] = 1
                if high[i] > ep[i - 1]:
                    ep[i] = high[i]
                    af[i] = min(af[i - 1] + af_start, af_max)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]
        else:  # Downtrend
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = ep[i - 1]
                ep[i] = high[i]
                af[i] = af_start
            else:
                trend[i] = -1
                if low[i] < ep[i - 1]:
                    ep[i] = low[i]
                    af[i] = min(af[i - 1] + af_start, af_max)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]

    return {
        "sar": round(float(sar[-1]), 2),
        "trend": "BULLISH" if trend[-1] == 1 else "BEARISH",
    }


def compute_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> dict:
    """SuperTrend indicator — ATR-based dynamic trend line."""
    high, low, close = df["High"], df["Low"], df["Close"]
    hl2 = (high + low) / 2
    atr = compute_atr_series(df, period)

    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=float)

    supertrend.iloc[0] = upper.iloc[0]
    direction.iloc[0] = 1

    for i in range(1, len(df)):
        if close.iloc[i] > upper.iloc[i - 1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i - 1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1]

        if direction.iloc[i] == 1:
            supertrend.iloc[i] = max(lower.iloc[i], supertrend.iloc[i - 1]) if direction.iloc[i - 1] == 1 else lower.iloc[i]
        else:
            supertrend.iloc[i] = min(upper.iloc[i], supertrend.iloc[i - 1]) if direction.iloc[i - 1] == -1 else upper.iloc[i]

    return {
        "supertrend": round(float(supertrend.iloc[-1]), 2),
        "signal": "BUY" if direction.iloc[-1] == 1 else "SELL",
    }


def compute_ichimoku(df: pd.DataFrame) -> dict:
    """Ichimoku Cloud (9, 26, 52)."""
    if len(df) < 52:
        return {"tenkan": 0, "kijun": 0, "senkouA": 0, "senkouB": 0, "signal": "NEUTRAL"}

    high, low, close = df["High"], df["Low"], df["Close"]
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)

    curr_price = close.iloc[-1]
    cloud_top = max(senkou_a.iloc[-1] if not np.isnan(senkou_a.iloc[-1]) else 0,
                    senkou_b.iloc[-1] if not np.isnan(senkou_b.iloc[-1]) else 0)
    cloud_bottom = min(senkou_a.iloc[-1] if not np.isnan(senkou_a.iloc[-1]) else 0,
                       senkou_b.iloc[-1] if not np.isnan(senkou_b.iloc[-1]) else 0)

    signal = "NEUTRAL"
    if curr_price > cloud_top and tenkan.iloc[-1] > kijun.iloc[-1]:
        signal = "STRONG_BULL"
    elif curr_price > cloud_top:
        signal = "BULL"
    elif curr_price < cloud_bottom and tenkan.iloc[-1] < kijun.iloc[-1]:
        signal = "STRONG_BEAR"
    elif curr_price < cloud_bottom:
        signal = "BEAR"

    return {
        "tenkan": round(float(tenkan.iloc[-1]), 2),
        "kijun": round(float(kijun.iloc[-1]), 2),
        "senkouA": round(float(senkou_a.iloc[-1]), 2) if not np.isnan(senkou_a.iloc[-1]) else 0,
        "senkouB": round(float(senkou_b.iloc[-1]), 2) if not np.isnan(senkou_b.iloc[-1]) else 0,
        "signal": signal,
    }


# ═══════════════════════════════════════════════════════════════
# CATEGORY 03 — MOMENTUM
# ═══════════════════════════════════════════════════════════════

def compute_rsi(df: pd.DataFrame, period: int = 14) -> dict:
    """Relative Strength Index."""
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = float(rsi.iloc[-1])
    return {
        "rsi": round(val, 2),
        "signal": "OVERBOUGHT" if val > 70 else "OVERSOLD" if val < 30 else "NEUTRAL",
        "divergence": _detect_rsi_divergence(df["Close"], rsi),
    }


def _detect_rsi_divergence(price: pd.Series, rsi: pd.Series) -> str:
    """Detect bullish/bearish RSI divergence."""
    if len(price) < 20:
        return "NONE"
    # Check last 20 bars
    p = price.tail(20)
    r = rsi.tail(20)
    if p.iloc[-1] < p.iloc[-10] and r.iloc[-1] > r.iloc[-10]:
        return "BULLISH"
    if p.iloc[-1] > p.iloc[-10] and r.iloc[-1] < r.iloc[-10]:
        return "BEARISH"
    return "NONE"


def compute_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> dict:
    """Stochastic Oscillator (%K, %D)."""
    low_min = df["Low"].rolling(k_period).min()
    high_max = df["High"].rolling(k_period).max()
    k = 100 * (df["Close"] - low_min) / (high_max - low_min).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return {
        "k": round(float(k.iloc[-1]), 2),
        "d": round(float(d.iloc[-1]), 2),
        "signal": "OVERBOUGHT" if k.iloc[-1] > 80 else "OVERSOLD" if k.iloc[-1] < 20 else "NEUTRAL",
    }


def compute_williams_r(df: pd.DataFrame, period: int = 14) -> dict:
    """Williams %R."""
    high_max = df["High"].rolling(period).max()
    low_min = df["Low"].rolling(period).min()
    wr = -100 * (high_max - df["Close"]) / (high_max - low_min).replace(0, np.nan)
    val = float(wr.iloc[-1])
    return {
        "williamsR": round(val, 2),
        "signal": "OVERBOUGHT" if val > -20 else "OVERSOLD" if val < -80 else "NEUTRAL",
    }


def compute_mfi(df: pd.DataFrame, period: int = 14) -> dict:
    """Money Flow Index — volume-weighted RSI."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    mf = tp * df["Volume"]
    pos_mf = mf.where(tp > tp.shift(1), 0).rolling(period).sum()
    neg_mf = mf.where(tp <= tp.shift(1), 0).rolling(period).sum()
    mr = pos_mf / neg_mf.replace(0, np.nan)
    mfi = 100 - (100 / (1 + mr))
    val = float(mfi.iloc[-1]) if not np.isnan(mfi.iloc[-1]) else 50
    return {
        "mfi": round(val, 2),
        "signal": "OVERBOUGHT" if val > 80 else "OVERSOLD" if val < 20 else "NEUTRAL",
    }


def compute_roc(df: pd.DataFrame, period: int = 12) -> dict:
    """Rate of Change."""
    roc = ((df["Close"] - df["Close"].shift(period)) / df["Close"].shift(period)) * 100
    return {"roc": round(float(roc.iloc[-1]), 2)}


def compute_cci(df: pd.DataFrame, period: int = 20) -> dict:
    """Commodity Channel Index."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    cci = (tp - sma) / (0.015 * mad).replace(0, np.nan)
    val = float(cci.iloc[-1]) if not np.isnan(cci.iloc[-1]) else 0
    return {
        "cci": round(val, 2),
        "signal": "OVERBOUGHT" if val > 100 else "OVERSOLD" if val < -100 else "NEUTRAL",
    }


# ═══════════════════════════════════════════════════════════════
# CATEGORY 04 — VOLATILITY
# ═══════════════════════════════════════════════════════════════

def compute_atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR as a series."""
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_atr(df: pd.DataFrame, period: int = 14) -> dict:
    """Average True Range."""
    atr = compute_atr_series(df, period)
    val = float(atr.iloc[-1])
    pct = val / df["Close"].iloc[-1] * 100
    return {
        "atr": round(val, 2),
        "atrPct": round(pct, 2),
    }


def compute_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> dict:
    """Bollinger Bands with %B and bandwidth."""
    close = df["Close"]
    sma = close.rolling(period).mean()
    rolling_std = close.rolling(period).std()
    upper = sma + std * rolling_std
    lower = sma - std * rolling_std

    curr_price = close.iloc[-1]
    bw = (upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1] * 100
    pct_b = (curr_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]) if (upper.iloc[-1] - lower.iloc[-1]) > 0 else 0.5

    # Squeeze detection
    avg_bw = ((upper - lower) / sma * 100).rolling(20).mean()
    is_squeeze = bw < float(avg_bw.iloc[-1]) * 0.75 if not np.isnan(avg_bw.iloc[-1]) else False

    return {
        "upper": round(float(upper.iloc[-1]), 2),
        "middle": round(float(sma.iloc[-1]), 2),
        "lower": round(float(lower.iloc[-1]), 2),
        "percentB": round(float(pct_b), 4),
        "bandwidth": round(float(bw), 2),
        "squeeze": bool(is_squeeze),
    }


def compute_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> dict:
    """Keltner Channels — EMA ± multiplier × ATR."""
    ema = compute_ema(df["Close"], period)
    atr = compute_atr_series(df, period)
    upper = ema + multiplier * atr
    lower = ema - multiplier * atr
    return {
        "upper": round(float(upper.iloc[-1]), 2),
        "middle": round(float(ema.iloc[-1]), 2),
        "lower": round(float(lower.iloc[-1]), 2),
    }


def compute_historical_volatility(df: pd.DataFrame, window: int = 30) -> dict:
    """Annualized historical volatility."""
    returns = df["Close"].pct_change().dropna()
    if len(returns) < window:
        return {"histVol": 0, "avgVol": 0, "volRatio": 1}
    curr_vol = float(returns.tail(window).std() * np.sqrt(252) * 100)
    avg_vol = float(returns.std() * np.sqrt(252) * 100)
    return {
        "histVol": round(curr_vol, 2),
        "avgVol": round(avg_vol, 2),
        "volRatio": round(curr_vol / max(avg_vol, 0.01), 2),
    }


# ═══════════════════════════════════════════════════════════════
# CATEGORY 05 — VOLUME ANALYSIS
# ═══════════════════════════════════════════════════════════════

def compute_vwap(df: pd.DataFrame) -> dict:
    """Volume-Weighted Average Price."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_vol = df["Volume"].cumsum()
    cum_tp_vol = (tp * df["Volume"]).cumsum()
    vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
    val = float(vwap.iloc[-1]) if not np.isnan(vwap.iloc[-1]) else df["Close"].iloc[-1]
    return {
        "vwap": round(val, 2),
        "priceVsVwap": "ABOVE" if df["Close"].iloc[-1] > val else "BELOW",
    }


def compute_obv(df: pd.DataFrame) -> dict:
    """On-Balance Volume."""
    obv = pd.Series(0, index=df.index, dtype=float)
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] + df["Volume"].iloc[i]
        elif df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] - df["Volume"].iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i - 1]

    obv_sma = obv.rolling(20).mean()
    return {
        "obv": round(float(obv.iloc[-1]), 0),
        "obvTrend": "RISING" if obv.iloc[-1] > obv_sma.iloc[-1] else "FALLING",
    }


def compute_ad_line(df: pd.DataFrame) -> dict:
    """Accumulation/Distribution Line."""
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]).replace(0, np.nan)
    mfm = mfm.fillna(0)
    mfv = mfm * df["Volume"]
    ad = mfv.cumsum()
    ad_sma = ad.rolling(20).mean()
    return {
        "adLine": round(float(ad.iloc[-1]), 0),
        "adTrend": "ACCUMULATION" if ad.iloc[-1] > ad_sma.iloc[-1] else "DISTRIBUTION",
    }


def compute_cmf(df: pd.DataFrame, period: int = 20) -> dict:
    """Chaikin Money Flow."""
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]).replace(0, np.nan)
    mfm = mfm.fillna(0)
    mfv = mfm * df["Volume"]
    cmf = mfv.rolling(period).sum() / df["Volume"].rolling(period).sum().replace(0, np.nan)
    val = float(cmf.iloc[-1]) if not np.isnan(cmf.iloc[-1]) else 0
    return {
        "cmf": round(val, 4),
        "signal": "BUYING_PRESSURE" if val > 0.05 else "SELLING_PRESSURE" if val < -0.05 else "NEUTRAL",
    }


def compute_relative_volume(df: pd.DataFrame, period: int = 20) -> dict:
    """Current volume vs 20-day SMA."""
    avg_vol = df["Volume"].rolling(period).mean()
    rel_vol = df["Volume"].iloc[-1] / avg_vol.iloc[-1] if avg_vol.iloc[-1] > 0 else 1
    return {
        "relativeVolume": round(float(rel_vol), 2),
        "anomaly": rel_vol > 2.0,
    }


# ═══════════════════════════════════════════════════════════════
# CATEGORY 06 — BEHAVIORAL FINANCE
# ═══════════════════════════════════════════════════════════════

def compute_herding_csad(returns_df: pd.DataFrame, regime: str = "NORMAL") -> dict:
    """
    Upgraded CCK CSAD with regime conditioning.
    CSAD_t = α + γ₁|R_m,t| + γ₂(R_m,t²) + γ₃·D_crisis·R_m,t² + ε_t
    """
    from scipy import stats as sp_stats

    if returns_df.empty or len(returns_df.columns) < 3:
        return {"herdingDetected": False, "intensity": 0, "gamma2": 0, "pValue": 1}

    market_return = returns_df.mean(axis=1)
    csad = returns_df.sub(market_return, axis=0).abs().mean(axis=1)
    abs_mkt = market_return.abs()
    mkt_sq = market_return ** 2

    # Crisis dummy variable
    d_crisis = 1 if regime in ("HIGH_VOL_CRISIS", "BEAR_TRENDING") else 0
    crisis_term = d_crisis * mkt_sq

    y = csad.values
    X = np.column_stack([np.ones(len(y)), abs_mkt.values, mkt_sq.values, crisis_term.values])

    try:
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        alpha, gamma1, gamma2, gamma3 = beta
        y_pred = X @ beta
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        n, k = len(y), 4
        mse = ss_res / max(n - k, 1)
        try:
            cov = mse * np.linalg.inv(X.T @ X)
            se = np.sqrt(np.diag(cov))
        except Exception:
            se = np.ones(4)

        t_stat = gamma2 / se[2] if se[2] > 0 else 0
        p_val = 2 * (1 - sp_stats.t.cdf(abs(t_stat), df=max(n - k, 1)))
        herding = gamma2 < 0 and p_val < 0.05
        intensity = min(100, abs(gamma2 / max(abs(gamma1), 1e-6)) * 100) if herding else max(0, min(20, abs(gamma2) * 1000))

        return {
            "herdingDetected": bool(herding),
            "intensity": round(float(intensity), 1),
            "gamma2": round(float(gamma2), 6),
            "gamma3": round(float(gamma3), 6),
            "pValue": round(float(p_val), 6),
            "rSquared": round(float(r_sq), 4),
            "observations": n,
            "regimeConditioned": d_crisis == 1,
        }
    except Exception as e:
        logger.error(f"Herding computation error: {e}")
        return {"herdingDetected": False, "intensity": 0, "gamma2": 0, "pValue": 1}


def compute_panic_score(df: pd.DataFrame) -> dict:
    """5-Factor Panic Score."""
    if df.empty or len(df) < 21:
        return {"panicScore": 0, "level": "CALM", "factors": {}}

    df = df.copy()
    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["Vol_SMA_20"] = df["Volume"].rolling(20).mean()
    vol_std = df["Volume"].rolling(20).std().replace(0, np.nan)
    df["Vol_Zscore"] = (df["Volume"] - df["Vol_SMA_20"]) / vol_std
    df["Volatility"] = df["Close"].pct_change().rolling(20).std() * np.sqrt(252) * 100

    # Factor 1: Volume anomalies
    panic_vol = ((df["Vol_Zscore"] > 2) & (df["Close"].pct_change() < -0.005)).sum()
    score_vol = min(100, float(panic_vol) / max(len(df), 1) * 500)

    # Factor 2: Delivery pressure proxy
    df["Range"] = (df["High"] - df["Low"]) / df["Close"].replace(0, np.nan) * 100
    avg_range = df["Range"].rolling(20).mean()
    spec = (df["Range"] / avg_range.replace(0, np.nan)).clip(0, 5)
    est_del = np.clip(100 - spec * 20, 10, 90)
    low_del = (est_del < 30).sum()
    score_del = min(100, float(low_del) / max(len(df), 1) * 200)

    # Factor 3: Price-volume divergence
    price_mom = df["Close"].pct_change(5)
    vol_mom = df["Volume"].pct_change(5)
    div_count = ((price_mom < -0.03) & (vol_mom > 0.3)).sum()
    score_div = min(100, float(div_count) / max(len(df), 1) * 500)

    # Factor 4: Drawdown
    peak = df["Close"].expanding().max()
    dd = (df["Close"] / peak - 1) * 100
    current_dd = abs(float(dd.iloc[-1]))
    score_dd = min(100, current_dd * 5)

    # Factor 5: Volatility regime
    curr_vol = float(df["Volatility"].dropna().iloc[-1]) if not df["Volatility"].dropna().empty else 0
    avg_vol = float(df["Volatility"].dropna().mean()) if not df["Volatility"].dropna().empty else 1
    score_vola = min(100, max(0, (curr_vol / max(avg_vol, 1) - 1) * 100))

    panic_score = round(
        score_vol * 0.30 + score_del * 0.20 + score_div * 0.25 + score_dd * 0.15 + score_vola * 0.10, 1
    )
    panic_score = min(100, max(0, panic_score))

    if panic_score >= 70: level = "EXTREME"
    elif panic_score >= 50: level = "HIGH"
    elif panic_score >= 30: level = "MODERATE"
    elif panic_score >= 10: level = "LOW"
    else: level = "CALM"

    return {
        "panicScore": panic_score,
        "level": level,
        "factors": {
            "volumeAnomaly": round(score_vol, 1),
            "deliveryPressure": round(score_del, 1),
            "priceVolDivergence": round(score_div, 1),
            "drawdownSeverity": round(score_dd, 1),
            "volatilityRegime": round(score_vola, 1),
        },
        "details": {
            "currentDrawdown": round(current_dd, 2),
            "currentVolatility": round(curr_vol, 2),
        },
    }


def compute_behavior_gap(df: pd.DataFrame) -> dict:
    """Behavior gap analysis — investment return vs investor return."""
    if df.empty or len(df) < 100:
        return {"investmentCagr": 0, "investorCagr": 0, "behaviorGap": 0}

    n_years = len(df) / 252
    bh_return = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
    bh_cagr = ((df["Close"].iloc[-1] / df["Close"].iloc[0]) ** (1 / max(n_years, 0.5)) - 1) * 100

    vol_norm = df["Volume"] / df["Volume"].mean()
    p_min, p_max = df["Close"].min(), df["Close"].max()
    p_range = p_max - p_min if p_max > p_min else 1.0
    price_norm = (df["Close"] - p_min) / p_range
    corr = float(vol_norm.corr(price_norm))
    gap = max(0, corr * bh_cagr * 0.4)
    investor_cagr = bh_cagr - gap

    return {
        "investmentReturn": round(bh_return, 2),
        "investmentCagr": round(bh_cagr, 2),
        "investorCagr": round(investor_cagr, 2),
        "behaviorGap": round(gap, 2),
        "periodYears": round(n_years, 1),
    }


# ═══════════════════════════════════════════════════════════════
# CATEGORY 07 — FUNDAMENTALS (computed in data_manager)
# ═══════════════════════════════════════════════════════════════

def compute_piotroski_f_score(fundamentals: dict) -> dict:
    """Compute Piotroski F-Score (0-9) from fundamental data."""
    score = 0
    details = {}

    # Profitability
    if fundamentals.get("roe", 0) > 0:
        score += 1; details["positiveROA"] = True
    if fundamentals.get("fcfYield", 0) > 0:
        score += 1; details["positiveCFO"] = True
    if fundamentals.get("epsGrowth", 0) > 0:
        score += 1; details["earningsGrowth"] = True
    # CFO > Net Income (proxy: FCF yield > 0 and positive)
    if fundamentals.get("fcfYield", 0) > 0.02:
        score += 1; details["qualityEarnings"] = True

    # Leverage
    if fundamentals.get("debtEquity", 999) < 100:
        score += 1; details["lowLeverage"] = True
    # Liquidity not available — assume pass
    score += 1; details["adequateLiquidity"] = True

    # Operating efficiency
    if fundamentals.get("revenueGrowth", 0) > 0:
        score += 1; details["revenueGrowth"] = True
    if fundamentals.get("roce", 0) > 0.1:
        score += 1; details["goodROCE"] = True
    # No share dilution data — assume pass for strong companies
    if score >= 5:
        score += 1; details["noShareDilution"] = True

    score = min(9, score)
    tier = "STRONG" if score >= 7 else "AVERAGE" if score >= 4 else "WEAK"

    return {"fScore": score, "tier": tier, "details": details}


# ═══════════════════════════════════════════════════════════════
# CATEGORY 08 — MULTI-TIMEFRAME CONFLUENCE
# ═══════════════════════════════════════════════════════════════

def compute_timeframe_signal(df: pd.DataFrame) -> str:
    """Compute a single BUY/SELL/HOLD signal from a dataframe."""
    if df.empty or len(df) < 30:
        return "HOLD"

    signals = []

    # EMA trend
    ema = compute_multi_ema(df)
    if ema["trend"] in ("STRONG_BULL", "BULL"):
        signals.append(1)
    elif ema["trend"] in ("STRONG_BEAR", "BEAR"):
        signals.append(-1)
    else:
        signals.append(0)

    # RSI
    rsi = compute_rsi(df)
    if rsi["rsi"] < 35:
        signals.append(1)  # Oversold = buy opportunity
    elif rsi["rsi"] > 65:
        signals.append(-1)
    else:
        signals.append(0)

    # MACD
    macd = compute_macd(df)
    if macd["histogram"] > 0:
        signals.append(1)
    elif macd["histogram"] < 0:
        signals.append(-1)
    else:
        signals.append(0)

    # SuperTrend
    if len(df) > 10:
        st = compute_supertrend(df)
        signals.append(1 if st["signal"] == "BUY" else -1)

    avg = sum(signals) / len(signals) if signals else 0
    if avg > 0.3:
        return "BUY"
    elif avg < -0.3:
        return "SELL"
    return "HOLD"


def compute_multi_timeframe_confluence(timeframe_data: dict[str, pd.DataFrame]) -> dict:
    """
    Compute signal across 15min, 1h, daily timeframes.
    Trade signal only when at least 2/3 timeframes align.
    """
    signals = {}
    for tf, df in timeframe_data.items():
        signals[tf] = compute_timeframe_signal(df)

    # Consensus
    buy_count = sum(1 for s in signals.values() if s == "BUY")
    sell_count = sum(1 for s in signals.values() if s == "SELL")

    if buy_count >= 2:
        consensus = "BUY"
    elif sell_count >= 2:
        consensus = "SELL"
    else:
        consensus = "HOLD"

    return {
        "timeframes": signals,
        "consensus": consensus,
        "alignment": max(buy_count, sell_count),
        "total": len(signals),
    }


# ═══════════════════════════════════════════════════════════════
# MASTER ANALYSIS — Compute All 40+ Indicators
# ═══════════════════════════════════════════════════════════════

def compute_full_analysis(df: pd.DataFrame, timeframe_data: dict | None = None) -> dict:
    """
    Compute ALL 40+ indicators from a single OHLCV dataframe.
    Returns a structured dict with all 8 categories.
    Each category is individually wrapped — one failure won't crash the pipeline.
    """
    if df.empty or len(df) < 30:
        return {"error": "Insufficient data", "indicators": {}}

    import logging
    _logger = logging.getLogger("tradeos.engine")

    result = {}

    # ── Price Action ──
    try:
        ha_df = compute_heikin_ashi(df)
        result["priceAction"] = {
            "heikinAshi": {"lastClose": round(float(ha_df["HA_Close"].iloc[-1]), 2)},
            "candlestickPatterns": detect_candlestick_patterns(df),
            "gaps": detect_price_gaps(df),
            "pivotPoints": compute_pivot_points(df),
        }
    except Exception as e:
        _logger.warning(f"Price action computation failed: {e}")
        result["priceAction"] = {
            "heikinAshi": {"lastClose": round(float(df["Close"].iloc[-1]), 2)},
            "candlestickPatterns": [],
            "gaps": [],
            "pivotPoints": {"pivot": round(float(df["Close"].iloc[-1]), 2), "r1": 0, "r2": 0, "s1": 0, "s2": 0},
        }

    # ── Trend ──
    try:
        result["trend"] = {
            "ema": compute_multi_ema(df),
            "macd": compute_macd(df),
            "adx": compute_adx(df),
            "parabolicSar": compute_parabolic_sar(df),
            "superTrend": compute_supertrend(df),
            "ichimoku": compute_ichimoku(df),
        }
    except Exception as e:
        _logger.warning(f"Trend computation failed: {e}")
        result["trend"] = {
            "ema": {"ema9": 0, "ema21": 0, "ema50": 0, "trend": "NEUTRAL"},
            "macd": {"macd": 0, "signal": 0, "histogram": 0, "crossover": "NONE"},
            "adx": {"adx": 0, "plusDI": 0, "minusDI": 0, "trendStrength": "WEAK"},
            "parabolicSar": {"sar": 0, "trend": "NEUTRAL"},
            "superTrend": {"superTrend": 0, "signal": "HOLD"},
            "ichimoku": {"tenkansen": 0, "kijunsen": 0, "signal": "NEUTRAL"},
        }

    # ── Momentum ──
    try:
        result["momentum"] = {
            "rsi": compute_rsi(df),
            "stochastic": compute_stochastic(df),
            "williamsR": compute_williams_r(df),
            "mfi": compute_mfi(df),
            "roc": compute_roc(df),
            "cci": compute_cci(df),
        }
    except Exception as e:
        _logger.warning(f"Momentum computation failed: {e}")
        result["momentum"] = {
            "rsi": {"rsi": 50, "signal": "NEUTRAL"},
            "stochastic": {"k": 50, "d": 50, "signal": "NEUTRAL"},
            "williamsR": {"williamsR": -50, "signal": "NEUTRAL"},
            "mfi": {"mfi": 50, "signal": "NEUTRAL"},
            "roc": {"roc": 0},
            "cci": {"cci": 0, "signal": "NEUTRAL"},
        }

    # ── Volatility ──
    try:
        result["volatility"] = {
            "bollingerBands": compute_bollinger_bands(df),
            "atr": compute_atr(df),
            "keltnerChannels": compute_keltner_channels(df),
            "historicalVol": compute_historical_volatility(df),
        }
    except Exception as e:
        _logger.warning(f"Volatility computation failed: {e}")
        result["volatility"] = {
            "bollingerBands": {"upper": 0, "middle": 0, "lower": 0, "percentB": 0.5, "squeeze": False},
            "atr": {"atr": 0, "atrPct": 0},
            "keltnerChannels": {"upper": 0, "middle": 0, "lower": 0},
            "historicalVol": {"histVol": 0, "volRatio": 1.0},
        }

    # ── Volume ──
    try:
        result["volume"] = {
            "vwap": compute_vwap(df),
            "obv": compute_obv(df),
            "adLine": compute_ad_line(df),
            "cmf": compute_cmf(df),
            "relativeVolume": compute_relative_volume(df),
        }
    except Exception as e:
        _logger.warning(f"Volume computation failed: {e}")
        result["volume"] = {
            "vwap": {"vwap": 0, "priceVsVwap": "AT"},
            "obv": {"obv": 0, "obvTrend": "FLAT"},
            "adLine": {"adLine": 0, "adTrend": "FLAT"},
            "cmf": {"cmf": 0, "signal": "NEUTRAL"},
            "relativeVolume": {"relativeVolume": 1.0, "anomaly": False},
        }

    # ── Behavioral ──
    try:
        result["behavioral"] = {
            "panicScore": compute_panic_score(df),
            "behaviorGap": compute_behavior_gap(df),
        }
    except Exception as e:
        _logger.warning(f"Behavioral computation failed: {e}")
        result["behavioral"] = {
            "panicScore": {"panicScore": 0, "level": "CALM", "factors": {}},
            "behaviorGap": {"gap": 0},
        }

    # Multi-timeframe if available
    if timeframe_data:
        try:
            result["multiTimeframe"] = compute_multi_timeframe_confluence(timeframe_data)
        except Exception as e:
            _logger.warning(f"Multi-timeframe computation failed: {e}")
            result["multiTimeframe"] = {"timeframes": {}, "consensus": "HOLD", "alignment": 0, "total": 0}

    return result

