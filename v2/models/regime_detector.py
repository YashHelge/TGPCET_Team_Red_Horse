"""
TradeOS V2 — HMM Regime Detector
Classifies market into 4 hidden states using Gaussian HMM:
  BULL_TRENDING | BEAR_TRENDING | LOW_VOL_RANGE | HIGH_VOL_CRISIS

Inputs: Return series, Volatility, ATR ratio, ADX, Volume ratio
"""

import numpy as np
import pandas as pd
import logging
import pickle
from pathlib import Path
from typing import Optional

logger = logging.getLogger("tradeos.regime")

REGIME_LABELS = {0: "BULL_TRENDING", 1: "BEAR_TRENDING", 2: "LOW_VOL_RANGE", 3: "HIGH_VOL_CRISIS"}


class RegimeDetector:
    """
    HMM-based market regime classifier.
    Uses sklearn GaussianMixture as a lightweight HMM alternative
    (hmmlearn is optional, falls back gracefully).
    """

    def __init__(self, n_states: int = 4, model_dir: Optional[Path] = None):
        self.n_states = n_states
        self.model_dir = model_dir
        self._model = None
        self._is_fitted = False
        self._state_mapping: dict[int, str] = {}

    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare feature matrix for HMM."""
        if len(df) < 30:
            return None

        features = pd.DataFrame(index=df.index)
        # Returns
        features["returns"] = df["Close"].pct_change()
        # Rolling volatility (20-day)
        features["volatility"] = features["returns"].rolling(20).std() * np.sqrt(252)
        # ATR ratio (current ATR / 50-day avg ATR)
        tr = pd.concat([
            df["High"] - df["Low"],
            abs(df["High"] - df["Close"].shift(1)),
            abs(df["Low"] - df["Close"].shift(1))
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        atr_50 = tr.rolling(50).mean()
        features["atr_ratio"] = atr / atr_50.replace(0, np.nan)
        # Volume ratio
        features["vol_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean().replace(0, np.nan)
        # Momentum (5-day returns)
        features["momentum"] = df["Close"].pct_change(5)

        features.dropna(inplace=True)
        if features.empty:
            return None

        # Normalize features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        return scaler.fit_transform(features.values), features.index

    def fit(self, df: pd.DataFrame) -> bool:
        """Train the regime classifier on historical data."""
        result = self._prepare_features(df)
        if result is None:
            return False
        X, idx = result

        try:
            # Try hmmlearn first
            try:
                from hmmlearn.hmm import GaussianHMM
                self._model = GaussianHMM(
                    n_components=self.n_states,
                    covariance_type="diag",
                    n_iter=200,
                    random_state=42,
                )
                self._model.fit(X)
                states = self._model.predict(X)
            except ImportError:
                # Fallback to GaussianMixture
                from sklearn.mixture import GaussianMixture
                self._model = GaussianMixture(
                    n_components=self.n_states,
                    covariance_type="diag",
                    max_iter=200,
                    random_state=42,
                )
                self._model.fit(X)
                states = self._model.predict(X)

            # Map states to labels based on characteristics
            self._map_states(X, states, df.loc[idx])
            self._is_fitted = True

            # Save model
            if self.model_dir:
                self.model_dir.mkdir(parents=True, exist_ok=True)
                with open(self.model_dir / "regime_model.pkl", "wb") as f:
                    pickle.dump({"model": self._model, "mapping": self._state_mapping}, f)

            return True
        except Exception as e:
            logger.error(f"Regime model training failed: {e}")
            return False

    def _map_states(self, X: np.ndarray, states: np.ndarray, df: pd.DataFrame):
        """Map HMM states to semantic labels based on statistical properties."""
        state_stats = {}
        for s in range(self.n_states):
            mask = states == s
            if mask.sum() == 0:
                continue
            state_stats[s] = {
                "mean_return": X[mask, 0].mean(),
                "mean_vol": X[mask, 1].mean(),
                "count": mask.sum(),
            }

        # Sort states by mean return and volatility
        sorted_states = sorted(state_stats.keys(), key=lambda s: state_stats[s]["mean_return"], reverse=True)

        # Assign labels
        mapping = {}
        if len(sorted_states) >= 4:
            # Highest return, low vol → BULL
            # Lowest return, high vol → CRISIS
            best = sorted_states[0]
            worst = sorted_states[-1]

            # Check volatility to distinguish RANGE from trends
            remaining = [s for s in sorted_states if s not in (best, worst)]
            if len(remaining) >= 2:
                # Lower vol → RANGE, higher return of remaining → ?
                if state_stats[remaining[0]]["mean_vol"] < state_stats[remaining[1]]["mean_vol"]:
                    range_state = remaining[0]
                    bear_state = remaining[1]
                else:
                    range_state = remaining[1]
                    bear_state = remaining[0]
            else:
                range_state = remaining[0] if remaining else 0
                bear_state = remaining[1] if len(remaining) > 1 else 1

            mapping[best] = "BULL_TRENDING"
            mapping[bear_state] = "BEAR_TRENDING"
            mapping[range_state] = "LOW_VOL_RANGE"
            mapping[worst] = "HIGH_VOL_CRISIS"
        else:
            for i, s in enumerate(sorted_states):
                mapping[s] = list(REGIME_LABELS.values())[i]

        self._state_mapping = mapping

    def predict(self, df: pd.DataFrame) -> dict:
        """Predict current regime."""
        if not self._is_fitted:
            # Try to train on the fly
            if not self.fit(df):
                return self._heuristic_regime(df)

        result = self._prepare_features(df)
        if result is None:
            return self._heuristic_regime(df)
        X, idx = result

        try:
            states = self._model.predict(X)
            current_state = int(states[-1])
            regime = self._state_mapping.get(current_state, "LOW_VOL_RANGE")

            # Compute probabilities if available
            try:
                if hasattr(self._model, 'predict_proba'):
                    proba = self._model.predict_proba(X[-1:])
                    state_probs = {
                        self._state_mapping.get(i, f"STATE_{i}"): round(float(p), 4)
                        for i, p in enumerate(proba[0])
                    }
                else:
                    state_probs = {regime: 1.0}
            except Exception:
                state_probs = {regime: 1.0}

            return {
                "regime": regime,
                "confidence": round(max(state_probs.values()), 4),
                "probabilities": state_probs,
                "method": "hmm" if "hmmlearn" in str(type(self._model)) else "gmm",
            }
        except Exception as e:
            logger.error(f"Regime prediction failed: {e}")
            return self._heuristic_regime(df)

    def _heuristic_regime(self, df: pd.DataFrame) -> dict:
        """Fallback heuristic regime detection when model fails."""
        if df.empty or len(df) < 20:
            return {"regime": "LOW_VOL_RANGE", "confidence": 0.3, "probabilities": {}, "method": "heuristic"}

        returns = df["Close"].pct_change().dropna()
        vol = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
        avg_vol = returns.std() * np.sqrt(252)
        trend = (df["Close"].iloc[-1] / df["Close"].iloc[-20] - 1)

        if vol > avg_vol * 1.5 and trend < -0.05:
            regime = "HIGH_VOL_CRISIS"
        elif trend > 0.03 and vol < avg_vol * 1.2:
            regime = "BULL_TRENDING"
        elif trend < -0.03:
            regime = "BEAR_TRENDING"
        else:
            regime = "LOW_VOL_RANGE"

        return {"regime": regime, "confidence": 0.5, "probabilities": {}, "method": "heuristic"}


# Singleton with lazy init
_detector: Optional[RegimeDetector] = None


def get_regime_detector() -> RegimeDetector:
    global _detector
    if _detector is None:
        from v2.config.settings import settings
        _detector = RegimeDetector(model_dir=settings.MODELS_DIR)
    return _detector
