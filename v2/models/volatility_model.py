"""
TradeOS V2 — GARCH Volatility Forecaster
GARCH(1,1) + EGARCH for next-period conditional variance forecasting.
Feeds position sizing, stop calibration, and signal filtering.
"""

import numpy as np
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger("tradeos.volatility_model")


class VolatilityForecaster:
    """
    GARCH(1,1) and EGARCH volatility forecasting.
    Falls back to exponentially weighted volatility if arch library unavailable.
    """

    def __init__(self):
        self._last_forecast: dict = {}

    def forecast(self, df: pd.DataFrame, horizon: int = 1) -> dict:
        """
        Forecast next-period volatility.
        Returns annualized vol, daily vol, vol ratio, and risk level.
        """
        if df.empty or len(df) < 60:
            return self._fallback_forecast(df)

        returns = df["Close"].pct_change().dropna() * 100  # Scale for GARCH

        if len(returns) < 50:
            return self._fallback_forecast(df)

        try:
            from arch import arch_model

            # GARCH(1,1)
            garch = arch_model(returns, vol="GARCH", p=1, q=1, dist="normal")
            garch_fit = garch.fit(disp="off", show_warning=False)
            garch_forecast = garch_fit.forecast(horizon=horizon)
            garch_var = float(garch_forecast.variance.values[-1, 0])
            garch_vol = np.sqrt(garch_var) / 100  # Back to decimal

            # EGARCH for leverage effect
            try:
                egarch = arch_model(returns, vol="EGARCH", p=1, q=1, dist="normal")
                egarch_fit = egarch.fit(disp="off", show_warning=False)
                egarch_forecast = egarch_fit.forecast(horizon=horizon)
                egarch_var = float(egarch_forecast.variance.values[-1, 0])
                egarch_vol = np.sqrt(egarch_var) / 100
            except Exception:
                egarch_vol = garch_vol

            # Average of GARCH and EGARCH
            forecast_vol = (garch_vol + egarch_vol) / 2
            annualized_vol = forecast_vol * np.sqrt(252)

            # Historical average for comparison
            hist_vol = float(returns.std() / 100) * np.sqrt(252)
            vol_ratio = annualized_vol / max(hist_vol, 0.001)

            # Risk level
            if vol_ratio > 1.5:
                risk_level = "HIGH"
            elif vol_ratio > 1.1:
                risk_level = "ELEVATED"
            elif vol_ratio < 0.7:
                risk_level = "LOW"
            else:
                risk_level = "NORMAL"

            result = {
                "forecastedVolDaily": round(forecast_vol, 6),
                "forecastedVolAnnualized": round(annualized_vol, 4),
                "historicalVolAnnualized": round(hist_vol, 4),
                "volRatio": round(vol_ratio, 4),
                "riskLevel": risk_level,
                "garchVol": round(garch_vol * np.sqrt(252), 4),
                "egarchVol": round(egarch_vol * np.sqrt(252), 4),
                "method": "garch_egarch",
            }
            self._last_forecast = result
            return result

        except ImportError:
            logger.info("arch library not available, using EWMA fallback")
            return self._fallback_forecast(df)
        except Exception as e:
            logger.error(f"GARCH forecast failed: {e}")
            return self._fallback_forecast(df)

    def _fallback_forecast(self, df: pd.DataFrame) -> dict:
        """Exponentially weighted moving average volatility when GARCH unavailable."""
        if df.empty or len(df) < 20:
            return {
                "forecastedVolDaily": 0.02, "forecastedVolAnnualized": 0.30,
                "historicalVolAnnualized": 0.30, "volRatio": 1.0,
                "riskLevel": "NORMAL", "method": "default",
            }

        returns = df["Close"].pct_change().dropna()
        ewma_vol = float(returns.ewm(span=20).std().iloc[-1])
        hist_vol = float(returns.std())
        annualized = ewma_vol * np.sqrt(252)
        hist_annualized = hist_vol * np.sqrt(252)
        vol_ratio = annualized / max(hist_annualized, 0.001)

        if vol_ratio > 1.5:
            risk_level = "HIGH"
        elif vol_ratio > 1.1:
            risk_level = "ELEVATED"
        elif vol_ratio < 0.7:
            risk_level = "LOW"
        else:
            risk_level = "NORMAL"

        return {
            "forecastedVolDaily": round(ewma_vol, 6),
            "forecastedVolAnnualized": round(annualized, 4),
            "historicalVolAnnualized": round(hist_annualized, 4),
            "volRatio": round(vol_ratio, 4),
            "riskLevel": risk_level,
            "method": "ewma",
        }


# Singleton
volatility_forecaster = VolatilityForecaster()
