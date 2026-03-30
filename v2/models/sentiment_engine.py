"""
TradeOS V2 — Custom Sentiment Engine
Hybrid sentiment analysis: keyword scoring + Groq LLaMA for complex analysis.
24-hour rolling window with recency decay.

No FinBERT GPU dependency — designed for production on any hardware.
"""

import asyncio
import math
import time
import logging
import re
from typing import Optional

import numpy as np

logger = logging.getLogger("tradeos.sentiment")

# ─── Keyword-Based Sentiment Scoring ──────────────────────────

POSITIVE_KEYWORDS = {
    # Strong positive (weight 3)
    "breakout": 3, "surge": 3, "rally": 3, "soar": 3, "boom": 3,
    "outperform": 3, "upgrade": 3, "beat estimates": 3, "record high": 3,
    "strong earnings": 3, "blockbuster": 3, "stellar": 3,
    # Medium positive (weight 2)
    "growth": 2, "profit": 2, "bullish": 2, "gain": 2, "rise": 2,
    "upbeat": 2, "positive": 2, "beat": 2, "exceed": 2, "robust": 2,
    "strong": 2, "improve": 2, "optimistic": 2, "expansion": 2,
    "dividend": 2, "buyback": 2, "acquisition": 2,
    # Mild positive (weight 1)
    "steady": 1, "stable": 1, "recovery": 1, "resilient": 1,
    "support": 1, "momentum": 1, "opportunity": 1, "attract": 1,
    "recommend": 1, "buy": 1, "overweight": 1,
}

NEGATIVE_KEYWORDS = {
    # Strong negative (weight -3)
    "crash": -3, "plunge": -3, "collapse": -3, "crisis": -3,
    "bankruptcy": -3, "fraud": -3, "scam": -3, "default": -3,
    "miss estimates": -3, "downgrade": -3, "delisting": -3,
    # Medium negative (weight -2)
    "decline": -2, "loss": -2, "bearish": -2, "selloff": -2,
    "fall": -2, "drop": -2, "weak": -2, "concern": -2,
    "risk": -2, "warning": -2, "cut": -2, "layoff": -2,
    "slowdown": -2, "inflation": -2, "recession": -2,
    # Mild negative (weight -1)
    "volatile": -1, "uncertainty": -1, "cautious": -1, "mixed": -1,
    "headwind": -1, "challenge": -1, "pressure": -1, "underweight": -1,
    "sell": -1, "overvalued": -1, "expensive": -1,
}


def keyword_sentiment_score(text: str) -> float:
    """
    Score text based on financial keyword matching.
    Returns score between -1.0 (very negative) and 1.0 (very positive).
    """
    if not text:
        return 0.0

    text_lower = text.lower()
    total_score = 0
    matches = 0

    for keyword, weight in {**POSITIVE_KEYWORDS, **NEGATIVE_KEYWORDS}.items():
        count = text_lower.count(keyword)
        if count > 0:
            total_score += weight * count
            matches += count

    if matches == 0:
        return 0.0

    # Normalize to [-1, 1] range using tanh
    raw = total_score / max(matches, 1)
    return round(max(-1.0, min(1.0, raw / 3)), 4)


# ─── Groq LLaMA Sentiment Analysis ────────────────────────────

async def llm_sentiment_score(text: str, api_key: str, model: str = "llama-3.3-70b-versatile") -> float:
    """
    Use Groq LLaMA to analyze sentiment of complex financial text.
    Returns score between -1.0 and 1.0.
    """
    if not api_key or not text:
        return 0.0

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        prompt = f"""Analyze the financial sentiment of this text. Rate it on a scale from -1.0 (very bearish/negative) to 1.0 (very bullish/positive). 
Consider: market impact, earnings implications, growth signals, risk factors.
Respond with ONLY a number between -1.0 and 1.0, nothing else.

Text: {text[:1000]}"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10,
        )

        score_text = response.choices[0].message.content.strip()
        score = float(re.search(r'-?[\d.]+', score_text).group())
        return round(max(-1.0, min(1.0, score)), 4)

    except Exception as e:
        logger.debug(f"LLM sentiment analysis failed: {e}")
        return 0.0


# ─── Sentiment Engine (with Decay) ─────────────────────────────

class SentimentEngine:
    """
    Hybrid sentiment engine combining keyword scoring + LLM analysis.
    24-hour rolling window with exponential recency decay.

    Sentiment_t = Σ(score_i × e^(-λ·age_i)) / N
    λ = 0.1 (decay constant — older news weighted less)
    """

    DECAY_LAMBDA = 0.1  # hours

    def __init__(self, groq_api_key: str = "", groq_model: str = "llama-3.3-70b-versatile"):
        self._api_key = groq_api_key
        self._model = groq_model
        self._cache: dict[str, dict] = {}  # symbol → {score, timestamp, articles}
        self._article_scores: dict[str, list] = {}  # symbol → [{score, timestamp}]

    async def analyze_articles(self, articles: list[dict], symbol: str) -> dict:
        """
        Analyze a list of news articles for sentiment.
        Returns aggregated score with decay weighting.
        """
        if not articles:
            return {
                "score": 0.0,
                "label": "NEUTRAL",
                "articleCount": 0,
                "confidence": 0.0,
            }

        scored_articles = []
        now = time.time()

        for article in articles:
            title = article.get("title", "")
            summary = article.get("summary", "")
            text = f"{title}. {summary}"
            article_time = article.get("datetime", now)

            # Keyword-based scoring (instant)
            keyword_score = keyword_sentiment_score(text)

            # LLM scoring for substantial articles (rate-limited)
            llm_score = 0.0
            if self._api_key and len(text) > 50:
                # Only use LLM for first 5 articles to respect rate limits
                if len(scored_articles) < 5:
                    llm_score = await llm_sentiment_score(text, self._api_key, self._model)
                    await asyncio.sleep(0.5)  # Rate limit cooldown

            # Hybrid score: 40% keyword + 60% LLM (if available)
            if llm_score != 0:
                final_score = 0.4 * keyword_score + 0.6 * llm_score
            else:
                final_score = keyword_score

            # Age in hours
            age_hours = max(0, (now - article_time) / 3600) if article_time > 0 else 12

            # Decay weight
            decay_weight = math.exp(-self.DECAY_LAMBDA * age_hours)

            scored_articles.append({
                "title": title[:100],
                "score": round(final_score, 4),
                "keywordScore": round(keyword_score, 4),
                "llmScore": round(llm_score, 4),
                "decayWeight": round(decay_weight, 4),
                "ageHours": round(age_hours, 1),
            })

        # Weighted aggregate
        if scored_articles:
            total_weight = sum(a["decayWeight"] for a in scored_articles)
            weighted_score = sum(a["score"] * a["decayWeight"] for a in scored_articles)
            aggregate = weighted_score / max(total_weight, 0.001)
        else:
            aggregate = 0.0

        # Confidence based on article count and agreement
        std = float(np.std([a["score"] for a in scored_articles])) if len(scored_articles) > 1 else 0.5
        confidence = min(1.0, len(scored_articles) / 10) * (1 - min(std, 1))

        # Label
        if aggregate > 0.3:
            label = "POSITIVE"
        elif aggregate > 0.1:
            label = "SLIGHTLY_POSITIVE"
        elif aggregate < -0.3:
            label = "NEGATIVE"
        elif aggregate < -0.1:
            label = "SLIGHTLY_NEGATIVE"
        else:
            label = "NEUTRAL"

        result = {
            "score": round(aggregate, 4),
            "label": label,
            "articleCount": len(scored_articles),
            "confidence": round(confidence, 4),
            "articles": scored_articles[:10],  # Top 10
        }

        self._cache[symbol] = {"data": result, "timestamp": now}
        return result

    def get_cached_sentiment(self, symbol: str) -> dict | None:
        """Get cached sentiment if fresh (< 15 min)."""
        if symbol in self._cache:
            entry = self._cache[symbol]
            if time.time() - entry["timestamp"] < 900:
                return entry["data"]
        return None



# Singleton
_sentiment_engine: Optional[SentimentEngine] = None


def get_sentiment_engine() -> SentimentEngine:
    global _sentiment_engine
    if _sentiment_engine is None:
        from v2.config.settings import settings
        _sentiment_engine = SentimentEngine(
            groq_api_key=settings.GROQ_API_KEY,
            groq_model=settings.GROQ_MODEL,
        )
    return _sentiment_engine
