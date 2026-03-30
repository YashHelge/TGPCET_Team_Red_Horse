"""
TradeOS V2 — Algorithmic Decision Engine
Pure mathematical trading decisions with optional LLM commentary.

Architecture:
  - All numbers (entry, SL, TP, position size) are computed algorithmically
  - LLM provides human-readable reasoning text ONLY (optional)
  - Decision uses Signal Confluence + ATR-based levels + Kelly Criterion

Expert Trader Logic:
  - Entry: current price (market) or nearest support (limit)
  - Stop Loss: ATR × 2 below entry (adapts to volatility)
  - Take Profit: ATR × 3 (target 1) and ATR × 5 (target 2) for 1.5:1 and 2.5:1 R:R
  - Position Size: Half-Kelly with regime + volatility adjustment
  - Never panic: crisis regime reduces position, doesn't flip randomly
"""

import asyncio
import logging
import json
import math
from typing import Optional

import numpy as np
import pandas as pd

from v2.config.settings import settings

logger = logging.getLogger("tradeos.decision")

# ─── System Prompt (commentary only) ─────────────────────────

COMMENTARY_PROMPT = """You are an institutional quantitative trading analyst. You are given the mathematical analysis results from our algorithmic system. Your job is to explain the decision in clear, professional language.

The DECISION (BUY/SELL/HOLD), entry price, stop loss, take profit, and position size have ALREADY been computed by mathematical models. Do NOT change or override them.

Your task:
1. Explain WHY the indicators support this decision (reference specific indicator values)
2. Highlight key risks and what to watch for (regime context, volatility)
3. Mention any conflicting signals that traders should monitor
4. Keep it to 3-5 sentences, professional and actionable

Respond in valid JSON:
{
  "reasoning": "Your 3-5 sentence explanation",
  "alerts": ["alert1", "alert2"],
  "keyDrivers": ["driver1", "driver2", "driver3"]
}"""


class AlgorithmicDecisionEngine:
    """
    Pure mathematical trading decision engine.
    All entry/SL/TP/sizing computed algorithmically.
    LLM is used ONLY for generating human-readable commentary.
    """

    def __init__(self):
        self._api_key = settings.GROQ_API_KEY
        self._model = settings.GROQ_MODEL

    async def generate_decision(
        self,
        symbol: str,
        current_price: float,
        indicators: dict,
        regime: dict,
        signal: dict,
        sentiment: dict,
        volatility: dict,
        fundamentals: dict,
        multi_tf: dict | None = None,
    ) -> dict:
        """Generate a complete trading decision using pure mathematics."""

        if current_price <= 0:
            return self._empty_decision(symbol, "No valid price data available")

        # ── Step 1: Compute ATR from indicators ─────────────────
        atr = self._get_atr(indicators, current_price)

        # ── Step 2: Compute key levels ──────────────────────────
        key_levels = self._compute_key_levels(indicators, current_price, atr)

        # ── Step 3: Signal confluence (weighted voting) ─────────
        confluence = self._compute_confluence(
            indicators, regime, signal, sentiment, volatility, fundamentals, multi_tf
        )

        # ── Step 4: Algorithmic action decision ─────────────────
        action = self._determine_action(confluence, regime, signal)

        # ── Step 5: ATR-based entry, SL, TP ─────────────────────
        entry, sl, tp1, tp2 = self._compute_levels(
            action, current_price, atr, key_levels
        )

        # ── Step 6: Kelly Criterion position sizing ─────────────
        position = self._compute_position_size(
            action, signal, volatility, regime, current_price, sl, tp1
        )

        # ── Step 7: Risk/Reward ratio ───────────────────────────
        rr_ratio = self._compute_risk_reward(action, entry, sl, tp1)

        # ── Step 8: Confidence from math ────────────────────────
        confidence = self._compute_confidence(confluence, signal, regime)

        # ── Step 9: Optional LLM commentary ─────────────────────
        commentary = await self._generate_commentary(
            symbol, action, confidence, current_price, entry, sl, tp1, tp2,
            confluence, signal, regime, sentiment, volatility, atr, indicators
        )

        decision = {
            "symbol": symbol,
            "action": action,
            "confidence": round(confidence, 2),
            "entry": {"price": round(entry, 2), "type": "MARKET" if action != "HOLD" else "NONE"},
            "stopLoss": round(sl, 2),
            "takeProfit1": round(tp1, 2),
            "takeProfit2": round(tp2, 2),
            "positionSizePct": round(position["sizePct"], 1),
            "riskReward": round(rr_ratio, 2),
            "reasoning": commentary.get("reasoning", self._math_reasoning(action, confluence, signal, regime)),
            "alerts": commentary.get("alerts", []),
            "keyDrivers": commentary.get("keyDrivers", []),
            "regime": regime.get("regime", "LOW_VOL_RANGE"),
            "confluenceScore": confluence["score"],
            "confluenceDetails": confluence["details"],
            "mathBasis": {
                "atr": round(atr, 2),
                "atrPct": round(atr / current_price * 100, 2),
                "supportLevel": round(key_levels["support"], 2),
                "resistanceLevel": round(key_levels["resistance"], 2),
                "kellyFraction": round(position["kelly"], 4),
                "signalConsensus": round(signal.get("consensusScore", 0), 4),
                "bullishCount": signal.get("bullishIndicators", 0),
                "bearishCount": signal.get("bearishIndicators", 0),
            },
        }

        return decision

    def _get_atr(self, indicators: dict, current_price: float) -> float:
        """Extract ATR from indicators or estimate from price."""
        try:
            vol_data = indicators.get("volatility", {})
            atr_data = vol_data.get("atr", {})
            atr = atr_data.get("atr", 0)
            if atr and float(atr) > 0:
                return float(atr)
        except (TypeError, ValueError):
            pass
        # Fallback: estimate ATR as 1.5% of price
        return current_price * 0.015

    def _compute_key_levels(self, indicators: dict, price: float, atr: float) -> dict:
        """Extract support/resistance from indicators."""
        pivots = indicators.get("priceAction", {}).get("pivotPoints", {})
        bb = indicators.get("volatility", {}).get("bollingerBands", {})
        vwap = indicators.get("volume", {}).get("vwap", {}).get("vwap", price)

        # Use pivot points, Bollinger bands, and VWAP for levels
        support_candidates = [
            pivots.get("s1", price - 2 * atr),
            bb.get("lower", price - 2 * atr),
            price - 2 * atr,
        ]
        resistance_candidates = [
            pivots.get("r1", price + 2 * atr),
            bb.get("upper", price + 2 * atr),
            price + 2 * atr,
        ]

        # Filter zero/None values
        support_candidates = [s for s in support_candidates if s and float(s) > 0]
        resistance_candidates = [r for r in resistance_candidates if r and float(r) > 0]

        support = min(support_candidates) if support_candidates else price - 2 * atr
        resistance = max(resistance_candidates) if resistance_candidates else price + 2 * atr

        return {
            "support": float(support),
            "resistance": float(resistance),
            "vwap": float(vwap) if vwap else price,
            "pivot": float(pivots.get("pivot", price)),
        }

    def _compute_confluence(
        self, indicators: dict, regime: dict, signal: dict,
        sentiment: dict, volatility: dict, fundamentals: dict,
        multi_tf: dict | None
    ) -> dict:
        """Signal Confluence: how many categories align."""
        details = {}
        score = 0

        # 1. Indicator Consensus (from signal model)
        consensus = signal.get("consensusScore", 0)
        if consensus > 0.15:
            details["consensus"] = "BULLISH"
            score += 2
        elif consensus < -0.15:
            details["consensus"] = "BEARISH"
            score -= 2
        else:
            details["consensus"] = "NEUTRAL"

        # 2. Trend
        trend_data = indicators.get("trend", {})
        ema = trend_data.get("ema", {})
        ema_trend = ema.get("trend", "NONE")
        if ema_trend in ("STRONG_BULL", "BULL"):
            details["trend"] = "BULL"
            score += 1
        elif ema_trend in ("STRONG_BEAR", "BEAR"):
            details["trend"] = "BEAR"
            score -= 1
        else:
            details["trend"] = "NEUTRAL"

        # 3. Volume Confirmation
        vol = indicators.get("volume", {})
        vwap_vs = vol.get("vwap", {}).get("priceVsVwap", "")
        obv_trend = vol.get("obv", {}).get("obvTrend", "")
        if vwap_vs == "ABOVE" and obv_trend == "RISING":
            details["volume"] = "ACCUMULATION"
            score += 1
        elif vwap_vs == "BELOW" and obv_trend == "FALLING":
            details["volume"] = "DISTRIBUTION"
            score -= 1
        else:
            details["volume"] = "NEUTRAL"

        # 4. Sentiment
        sent_score = sentiment.get("score", 0)
        if sent_score > 0.15:
            details["sentiment"] = "POSITIVE"
            score += 1
        elif sent_score < -0.15:
            details["sentiment"] = "NEGATIVE"
            score -= 1
        else:
            details["sentiment"] = "NEUTRAL"

        # 5. Volatility Regime
        risk_level = volatility.get("riskLevel", "NORMAL")
        if risk_level == "LOW":
            details["volatility"] = "FAVORABLE"
            score += 1
        elif risk_level in ("HIGH", "EXTREME"):
            details["volatility"] = "RISKY"
            score -= 1
        else:
            details["volatility"] = "NORMAL"

        # 6. Multi-Timeframe Alignment
        if multi_tf:
            tfs = multi_tf.get("timeframes", {})
            if isinstance(tfs, dict):
                buy_count = sum(1 for v in tfs.values() if v == "BUY")
                sell_count = sum(1 for v in tfs.values() if v == "SELL")
                if buy_count >= 2:
                    details["multiTF"] = "ALIGNED_BULL"
                    score += 1
                elif sell_count >= 2:
                    details["multiTF"] = "ALIGNED_BEAR"
                    score -= 1
                else:
                    details["multiTF"] = "MIXED"
            else:
                details["multiTF"] = "N/A"
        else:
            details["multiTF"] = "N/A"

        return {"score": score, "details": details}

    def _determine_action(self, confluence: dict, regime: dict, signal: dict) -> str:
        """Determine BUY/SELL/HOLD using aggregate conviction score.

        Combines:
          - Indicator consensus score (-1 to +1): the math from 12 weighted indicators
          - Confluence score: how many analysis categories align
          - Signal probabilities: raw P(BUY) vs P(SELL)

        Like an expert trader: only acts when multiple independent signals agree.
        """
        consensus_score = signal.get("consensusScore", 0)
        conf_score = confluence["score"]
        regime_name = regime.get("regime", "LOW_VOL_RANGE")

        # Signal probability edge
        probs = signal.get("probabilities", {})
        p_buy = probs.get("BUY", 0.33)
        p_sell = probs.get("SELL", 0.33)
        prob_edge = p_buy - p_sell  # Positive = buy lean, negative = sell lean

        # Aggregate conviction: weighted combination
        conviction = (
            consensus_score * 3.0 +    # Primary: indicator math
            conf_score * 0.5 +          # Secondary: category confluence
            prob_edge * 2.0             # Tertiary: probability edge
        )

        # Regime-adjusted thresholds (expert trader doesn't panic)
        if regime_name == "HIGH_VOL_CRISIS":
            buy_threshold = 2.5    # Much higher bar in crisis
            sell_threshold = -2.5
        elif regime_name == "BEAR_TRENDING":
            buy_threshold = 2.0    # Slightly cautious in bear
            sell_threshold = -1.2  # Easier to sell
        elif regime_name == "BULL_TRENDING":
            buy_threshold = 1.0    # Easier to buy in bull
            sell_threshold = -1.8  # Harder to sell
        else:  # LOW_VOL_RANGE
            buy_threshold = 1.5
            sell_threshold = -1.5

        if conviction >= buy_threshold:
            return "BUY"
        elif conviction <= sell_threshold:
            return "SELL"
        return "HOLD"

    def _compute_levels(
        self, action: str, price: float, atr: float, key_levels: dict
    ) -> tuple:
        """Compute entry, stop loss, take profit using ATR mathematics."""
        if action == "HOLD":
            return price, price, price, price

        if action == "BUY":
            entry = price
            # SL = 2 × ATR below entry (risk)
            sl = max(entry - 2 * atr, key_levels["support"] * 0.99)
            # TP1 = 3 × ATR above entry (1.5:1 R:R)
            tp1 = entry + 3 * atr
            # TP2 = 5 × ATR above entry (2.5:1 R:R) or resistance
            tp2 = max(entry + 5 * atr, key_levels["resistance"])
        else:  # SELL
            entry = price
            sl = min(entry + 2 * atr, key_levels["resistance"] * 1.01)
            tp1 = entry - 3 * atr
            tp2 = min(entry - 5 * atr, key_levels["support"])

        return entry, sl, tp1, tp2

    def _compute_position_size(
        self, action: str, signal: dict, volatility: dict,
        regime: dict, price: float, sl: float, tp: float,
    ) -> dict:
        """Half-Kelly position sizing with volatility adjustment."""
        if action == "HOLD":
            return {"sizePct": 0.0, "kelly": 0.0}

        # Win probability from indicator consensus
        probs = signal.get("probabilities", {})
        win_prob = probs.get("BUY", 0.5) if action == "BUY" else probs.get("SELL", 0.5)

        # Risk and reward from computed levels
        risk = abs(price - sl) / price  # Risk as percentage
        reward = abs(tp - price) / price  # Reward as percentage

        if risk == 0:
            risk = 0.02  # Minimum 2% risk
        if reward == 0:
            reward = 0.03

        rr = reward / risk

        # Kelly Criterion: f* = (p * b - q) / b where b = R:R ratio
        q = 1 - win_prob
        kelly = (win_prob * rr - q) / max(rr, 0.01)
        half_kelly = max(0, kelly / 2)

        # Volatility adjustment
        vol_ratio = volatility.get("volRatio", 1.0)
        vol_adjusted = half_kelly * (1 / max(float(vol_ratio) if vol_ratio else 1.0, 0.5))

        # Regime-based position limits
        regime_name = regime.get("regime", "LOW_VOL_RANGE")
        max_pct = settings.MAX_POSITION_PCT
        if regime_name == "HIGH_VOL_CRISIS":
            max_pct = settings.CRISIS_MAX_POSITION

        size_pct = max(0.5, min(max_pct, vol_adjusted * 100))

        return {"sizePct": size_pct, "kelly": half_kelly}

    def _compute_risk_reward(self, action: str, entry: float, sl: float, tp: float) -> float:
        """Compute R:R ratio."""
        if action == "HOLD":
            return 0.0
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk == 0:
            return 0.0
        return reward / risk

    def _compute_confidence(self, confluence: dict, signal: dict, regime: dict) -> float:
        """Compute overall confidence from mathematical inputs."""
        base = signal.get("confidence", 0.5)
        confluence_boost = min(0.15, abs(confluence["score"]) * 0.025)
        regime_name = regime.get("regime", "LOW_VOL_RANGE")

        # Crisis regime reduces confidence
        if regime_name == "HIGH_VOL_CRISIS":
            return max(0.2, base * 0.7 + confluence_boost)

        return min(0.95, base + confluence_boost)

    def _math_reasoning(self, action: str, confluence: dict, signal: dict, regime: dict) -> str:
        """Generate reasoning from math when LLM is unavailable."""
        score = confluence["score"]
        details = confluence["details"]
        consensus = signal.get("consensusScore", 0)
        bullish = signal.get("bullishIndicators", 0)
        bearish = signal.get("bearishIndicators", 0)
        regime_name = regime.get("regime", "LOW_VOL_RANGE")

        parts = []
        parts.append(f"Confluence score {score}/6 in {regime_name} regime.")
        parts.append(f"Indicator consensus: {bullish} bullish, {bearish} bearish (score: {consensus:.2f}).")

        aligned = [k for k, v in details.items() if v in ("BULLISH", "BULL", "ACCUMULATION", "POSITIVE", "FAVORABLE", "ALIGNED_BULL")]
        opposed = [k for k, v in details.items() if v in ("BEARISH", "BEAR", "DISTRIBUTION", "NEGATIVE", "RISKY", "ALIGNED_BEAR")]

        if aligned:
            parts.append(f"Supporting: {', '.join(aligned)}.")
        if opposed:
            parts.append(f"Opposing: {', '.join(opposed)}.")

        if action == "HOLD":
            parts.append("Insufficient alignment for a directional trade — holding.")

        return " ".join(parts)

    async def _generate_commentary(
        self, symbol, action, confidence, price, entry, sl, tp1, tp2,
        confluence, signal, regime, sentiment, volatility, atr, indicators
    ) -> dict:
        """Optional LLM commentary — explains the math, doesn't make the decision."""
        if not self._api_key:
            return {}

        try:
            from groq import Groq
            client = Groq(api_key=self._api_key)

            context = {
                "symbol": symbol,
                "COMPUTED_ACTION": action,
                "confidence": confidence,
                "currentPrice": price,
                "entry": entry,
                "stopLoss": sl,
                "takeProfit": tp1,
                "atr": round(atr, 2),
                "atrPct": round(atr / price * 100, 2),
                "regime": regime.get("regime", "LOW_VOL_RANGE"),
                "confluenceScore": confluence["score"],
                "confluenceDetails": confluence["details"],
                "consensusScore": signal.get("consensusScore", 0),
                "bullishIndicators": signal.get("bullishIndicators", 0),
                "bearishIndicators": signal.get("bearishIndicators", 0),
                "indicatorBreakdown": signal.get("indicatorBreakdown", {}),
                "sentimentScore": sentiment.get("score", 0),
                "sentimentLabel": sentiment.get("label", "NEUTRAL"),
                "volRiskLevel": volatility.get("riskLevel", "NORMAL"),
            }

            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": COMMENTARY_PROMPT},
                    {"role": "user", "content": f"Explain this algorithmic trading decision:\n{json.dumps(context, indent=2, default=str)}"},
                ],
                temperature=0.3,
                max_tokens=512,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.warning(f"LLM commentary generation failed (non-critical): {e}")
            return {}

    def _empty_decision(self, symbol: str, reason: str) -> dict:
        return {
            "symbol": symbol,
            "action": "HOLD",
            "confidence": 0.0,
            "entry": {"price": 0, "type": "NONE"},
            "stopLoss": 0,
            "takeProfit1": 0,
            "takeProfit2": 0,
            "positionSizePct": 0,
            "riskReward": 0,
            "reasoning": reason,
            "alerts": [reason],
            "keyDrivers": [],
            "regime": "UNKNOWN",
            "confluenceScore": 0,
            "confluenceDetails": {},
            "mathBasis": {},
        }


# Singleton
decision_synthesizer = AlgorithmicDecisionEngine()
