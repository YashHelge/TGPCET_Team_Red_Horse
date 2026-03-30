"""
TradeOS V2 — Indicator Consensus Signal Model
Pure mathematical signal generation using weighted indicator voting.

Replaces unreliable ML prediction with deterministic, transparent math.
Each indicator contributes a weighted vote toward BUY/SELL/HOLD.

Architecture:
  1. Compute 12 individual indicator signals (each returns -1 to +1)
  2. Apply category weights (trend=2x, momentum=1.5x, volume=1.5x, etc.)
  3. Normalize into P(BUY), P(SELL), P(HOLD) probabilities
  4. Action = highest probability with confidence threshold

Think like an expert trader:
  - Never panic (volatility-adjusted weights)
  - Confirm with volume (no conviction without volume confirmation)
  - Respect the trend (higher weight on trend alignment)
  - Multi-timeframe agreement = higher confidence
"""

import numpy as np
import pandas as pd
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("tradeos.signal_model")


class IndicatorConsensus:
    """
    Weighted indicator voting system for signal generation.
    Each indicator produces a score from -1 (strong sell) to +1 (strong buy).
    Final signal is the weighted average of all indicator scores.
    """

    def compute(self, df: pd.DataFrame, regime: str = "LOW_VOL_RANGE") -> dict:
        """Compute consensus signal from all indicators."""
        if df.empty or len(df) < 30:
            return self._neutral()

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        signals = {}

        # ── 1. EMA Alignment (weight: 2.0) ──────────────────────────
        try:
            ema9 = close.ewm(span=9, adjust=False).mean()
            ema21 = close.ewm(span=21, adjust=False).mean()
            ema50 = close.ewm(span=50, adjust=False).mean()

            price = float(close.iloc[-1])
            e9 = float(ema9.iloc[-1])
            e21 = float(ema21.iloc[-1])
            e50 = float(ema50.iloc[-1])

            # Perfect bull: price > ema9 > ema21 > ema50
            if price > e9 > e21 > e50:
                signals["ema_alignment"] = 1.0
            elif price > e9 > e21:
                signals["ema_alignment"] = 0.6
            elif price > e21:
                signals["ema_alignment"] = 0.3
            # Perfect bear: price < ema9 < ema21 < ema50
            elif price < e9 < e21 < e50:
                signals["ema_alignment"] = -1.0
            elif price < e9 < e21:
                signals["ema_alignment"] = -0.6
            elif price < e21:
                signals["ema_alignment"] = -0.3
            else:
                signals["ema_alignment"] = 0.0
        except Exception:
            signals["ema_alignment"] = 0.0

        # ── 2. MACD Histogram (weight: 1.5) ─────────────────────────
        try:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal_line = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal_line

            h_now = float(hist.iloc[-1])
            h_prev = float(hist.iloc[-2])

            # Histogram increasing = bullish, decreasing = bearish
            if h_now > 0 and h_now > h_prev:
                signals["macd"] = 0.8
            elif h_now > 0:
                signals["macd"] = 0.3
            elif h_now < 0 and h_now < h_prev:
                signals["macd"] = -0.8
            elif h_now < 0:
                signals["macd"] = -0.3
            else:
                signals["macd"] = 0.0
        except Exception:
            signals["macd"] = 0.0

        # ── 3. RSI (weight: 1.5) ─────────────────────────────────────
        try:
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            rsi_val = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50

            if rsi_val < 25:
                signals["rsi"] = 0.9  # Deeply oversold = strong buy
            elif rsi_val < 35:
                signals["rsi"] = 0.5  # Mildly oversold
            elif rsi_val > 75:
                signals["rsi"] = -0.9  # Deeply overbought = strong sell
            elif rsi_val > 65:
                signals["rsi"] = -0.5  # Mildly overbought
            elif 45 <= rsi_val <= 55:
                signals["rsi"] = 0.0  # Neutral zone
            else:
                signals["rsi"] = (50 - rsi_val) / 50 * 0.3  # Slight lean
        except Exception:
            signals["rsi"] = 0.0

        # ── 4. Stochastic K/D (weight: 1.0) ──────────────────────────
        try:
            low14 = low.rolling(14).min()
            high14 = high.rolling(14).max()
            k = ((close - low14) / (high14 - low14).replace(0, np.nan)) * 100
            d = k.rolling(3).mean()

            k_val = float(k.iloc[-1])
            d_val = float(d.iloc[-1])

            if k_val < 20 and k_val > d_val:  # Oversold + K crossing above D
                signals["stochastic"] = 0.8
            elif k_val < 30:
                signals["stochastic"] = 0.4
            elif k_val > 80 and k_val < d_val:  # Overbought + K crossing below D
                signals["stochastic"] = -0.8
            elif k_val > 70:
                signals["stochastic"] = -0.4
            else:
                signals["stochastic"] = 0.0
        except Exception:
            signals["stochastic"] = 0.0

        # ── 5. SuperTrend (weight: 1.0) ──────────────────────────────
        try:
            tr = pd.concat([
                high - low,
                abs(high - close.shift(1)),
                abs(low - close.shift(1))
            ], axis=1).max(axis=1)
            atr = tr.rolling(10).mean()

            hl2 = (high + low) / 2
            upper = hl2 + 3 * atr
            lower = hl2 - 3 * atr

            price_val = float(close.iloc[-1])
            up_val = float(upper.iloc[-1])
            low_val = float(lower.iloc[-1])

            if price_val > up_val:
                signals["supertrend"] = -0.5  # Overextended
            elif price_val > low_val:
                signals["supertrend"] = 0.5  # Bullish
            else:
                signals["supertrend"] = -0.5  # Bearish
        except Exception:
            signals["supertrend"] = 0.0

        # ── 6. OBV Trend (weight: 1.5) ──────────────────────────────
        try:
            obv = pd.Series(0.0, index=df.index, dtype=float)
            for i in range(1, len(df)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]

            obv_sma = obv.rolling(20).mean()
            obv_now = float(obv.iloc[-1])
            obv_sma_now = float(obv_sma.iloc[-1])
            obv_slope = float(obv.diff(5).iloc[-1])

            if obv_now > obv_sma_now and obv_slope > 0:
                signals["obv"] = 0.7  # Accumulation
            elif obv_now < obv_sma_now and obv_slope < 0:
                signals["obv"] = -0.7  # Distribution
            else:
                signals["obv"] = 0.0
        except Exception:
            signals["obv"] = 0.0

        # ── 7. VWAP Position (weight: 1.0) ───────────────────────────
        try:
            tp = (high + low + close) / 3
            vwap = (tp * volume).cumsum() / volume.cumsum()
            vwap_val = float(vwap.iloc[-1])
            price_val = float(close.iloc[-1])

            diff_pct = (price_val - vwap_val) / vwap_val * 100
            if diff_pct > 1.5:
                signals["vwap"] = 0.5
            elif diff_pct < -1.5:
                signals["vwap"] = -0.5
            else:
                signals["vwap"] = diff_pct / 3  # Scaled signal
        except Exception:
            signals["vwap"] = 0.0

        # ── 8. Bollinger Band Position (weight: 1.0) ─────────────────
        try:
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            upper_bb = sma20 + 2 * std20
            lower_bb = sma20 - 2 * std20
            pctb = (close - lower_bb) / (upper_bb - lower_bb).replace(0, np.nan)

            pctb_val = float(pctb.iloc[-1])

            if pctb_val < 0.05:
                signals["bollinger"] = 0.8  # Below lower band = oversold
            elif pctb_val < 0.2:
                signals["bollinger"] = 0.4
            elif pctb_val > 0.95:
                signals["bollinger"] = -0.8  # Above upper band = overbought
            elif pctb_val > 0.8:
                signals["bollinger"] = -0.4
            else:
                signals["bollinger"] = 0.0
        except Exception:
            signals["bollinger"] = 0.0

        # ── 9. Volume Anomaly (weight: 1.0) ──────────────────────────
        try:
            vol_sma = volume.rolling(20).mean()
            rel_vol = float(volume.iloc[-1] / vol_sma.iloc[-1])

            # High volume confirms the move
            price_change = float(close.pct_change().iloc[-1])
            if rel_vol > 1.5 and price_change > 0:
                signals["volume_anomaly"] = 0.6
            elif rel_vol > 1.5 and price_change < 0:
                signals["volume_anomaly"] = -0.6
            else:
                signals["volume_anomaly"] = 0.0
        except Exception:
            signals["volume_anomaly"] = 0.0

        # ── 10. Price Momentum (5d + 20d) (weight: 1.0) ─────────────
        try:
            mom5 = float(close.pct_change(5).iloc[-1])
            mom20 = float(close.pct_change(20).iloc[-1])

            # Combined short + medium term momentum
            if mom5 > 0.02 and mom20 > 0.03:
                signals["momentum"] = 0.7
            elif mom5 > 0 and mom20 > 0:
                signals["momentum"] = 0.3
            elif mom5 < -0.02 and mom20 < -0.03:
                signals["momentum"] = -0.7
            elif mom5 < 0 and mom20 < 0:
                signals["momentum"] = -0.3
            else:
                signals["momentum"] = 0.0
        except Exception:
            signals["momentum"] = 0.0

        # ── 11. ADX Strength (weight: 0.5) ───────────────────────────
        try:
            tr = pd.concat([
                high - low,
                abs(high - close.shift(1)),
                abs(low - close.shift(1))
            ], axis=1).max(axis=1)
            atr14 = tr.rolling(14).mean()

            plus_dm = (high.diff()).where(
                (high.diff() > 0) & (high.diff() > -low.diff()), 0.0
            ).rolling(14).mean()
            minus_dm = (-low.diff()).where(
                (-low.diff() > 0) & (-low.diff() > high.diff()), 0.0
            ).rolling(14).mean()

            plus_di = (plus_dm / atr14.replace(0, np.nan)) * 100
            minus_di = (minus_dm / atr14.replace(0, np.nan)) * 100
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
            adx = dx.rolling(14).mean()

            adx_val = float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else 20
            pdi = float(plus_di.iloc[-1]) if not np.isnan(plus_di.iloc[-1]) else 0
            mdi = float(minus_di.iloc[-1]) if not np.isnan(minus_di.iloc[-1]) else 0

            if adx_val > 25:  # Strong trend
                if pdi > mdi:
                    signals["adx"] = 0.5
                else:
                    signals["adx"] = -0.5
            else:
                signals["adx"] = 0.0  # No clear trend
        except Exception:
            signals["adx"] = 0.0

        # ── 12. MFI (weight: 1.0) ────────────────────────────────────
        try:
            tp = (high + low + close) / 3
            mf = tp * volume
            pos_mf = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
            neg_mf = mf.where(tp <= tp.shift(1), 0).rolling(14).sum()
            mr = pos_mf / neg_mf.replace(0, np.nan)
            mfi = 100 - (100 / (1 + mr))
            mfi_val = float(mfi.iloc[-1]) if not np.isnan(mfi.iloc[-1]) else 50

            if mfi_val < 20:
                signals["mfi"] = 0.7  # Oversold on money flow
            elif mfi_val > 80:
                signals["mfi"] = -0.7  # Overbought on money flow
            else:
                signals["mfi"] = (50 - mfi_val) / 70 * 0.3
        except Exception:
            signals["mfi"] = 0.0

        # ─── Weighted Aggregation ────────────────────────────────────
        weights = {
            "ema_alignment": 2.0,
            "macd": 1.5,
            "rsi": 1.5,
            "stochastic": 1.0,
            "supertrend": 1.0,
            "obv": 1.5,
            "vwap": 1.0,
            "bollinger": 1.0,
            "volume_anomaly": 1.0,
            "momentum": 1.0,
            "adx": 0.5,
            "mfi": 1.0,
        }

        # Regime-adjusted weights: in crisis, increase caution
        if regime == "HIGH_VOL_CRISIS":
            weights["rsi"] *= 1.5      # Oversold matters more in crisis
            weights["bollinger"] *= 1.5
            weights["momentum"] *= 0.5  # Momentum less reliable in crisis
            weights["volume_anomaly"] *= 1.5  # Volume spikes matter more

        total_weight = sum(weights.values())
        weighted_score = sum(signals.get(k, 0) * w for k, w in weights.items())
        normalized_score = weighted_score / total_weight  # Range: -1 to +1

        # Convert to probabilities
        if normalized_score > 0:
            p_buy = 0.33 + normalized_score * 0.5
            p_sell = max(0.05, 0.33 - normalized_score * 0.4)
            p_hold = 1.0 - p_buy - p_sell
        elif normalized_score < 0:
            p_sell = 0.33 + abs(normalized_score) * 0.5
            p_buy = max(0.05, 0.33 - abs(normalized_score) * 0.4)
            p_hold = 1.0 - p_buy - p_sell
        else:
            p_buy = 0.25
            p_sell = 0.25
            p_hold = 0.50

        # Ensure valid probabilities
        total = p_buy + p_sell + p_hold
        p_buy /= total
        p_sell /= total
        p_hold /= total

        probabilities = {
            "BUY": round(p_buy, 4),
            "SELL": round(p_sell, 4),
            "HOLD": round(p_hold, 4),
        }

        # Determine action with confidence threshold
        action = max(probabilities, key=probabilities.get)
        confidence = probabilities[action]

        # Don't act on weak signals
        if confidence < 0.45:
            action = "HOLD"
            confidence = probabilities["HOLD"]

        # Count supporting indicators
        bullish = sum(1 for v in signals.values() if v > 0.2)
        bearish = sum(1 for v in signals.values() if v < -0.2)

        return {
            "action": action,
            "probabilities": probabilities,
            "confidence": round(confidence, 4),
            "method": "indicator_consensus",
            "consensusScore": round(normalized_score, 4),
            "bullishIndicators": bullish,
            "bearishIndicators": bearish,
            "totalIndicators": len(signals),
            "indicatorBreakdown": {k: round(v, 3) for k, v in signals.items()},
        }

    def _neutral(self) -> dict:
        return {
            "action": "HOLD",
            "probabilities": {"BUY": 0.25, "SELL": 0.25, "HOLD": 0.50},
            "confidence": 0.50,
            "method": "indicator_consensus",
            "consensusScore": 0.0,
            "bullishIndicators": 0,
            "bearishIndicators": 0,
            "totalIndicators": 0,
            "indicatorBreakdown": {},
        }


# ─── Backward-Compatible Wrapper ──────────────────────────────

class SignalModel:
    """Backward-compatible wrapper using IndicatorConsensus."""

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir
        self._consensus = IndicatorConsensus()

    def predict(self, df: pd.DataFrame, regime: str = "LOW_VOL_RANGE") -> dict:
        """Generate signal using indicator consensus (pure math)."""
        return self._consensus.compute(df, regime)

    def train(self, df: pd.DataFrame, regime: str = "LOW_VOL_RANGE") -> bool:
        """No training needed — consensus is deterministic."""
        return True


# Singleton
_signal_model: Optional[SignalModel] = None


def get_signal_model() -> SignalModel:
    global _signal_model
    if _signal_model is None:
        from v2.config.settings import settings
        _signal_model = SignalModel(model_dir=settings.MODELS_DIR)
    return _signal_model
