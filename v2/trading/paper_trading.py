"""
TradeOS V2 — Paper Trading Engine
Virtual portfolio management with real-time position monitoring,
auto-exit conditions, P&L tracking, and performance analytics.
"""

import uuid
import time
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np

from v2.config.settings import settings

logger = logging.getLogger("tradeos.paper_trading")


@dataclass
class Position:
    """A single paper trading position."""
    id: str = ""
    symbol: str = ""
    action: str = "BUY"  # BUY or SELL (short)
    entry_price: float = 0
    current_price: float = 0
    quantity: float = 0
    stop_loss: float = 0
    take_profit_1: float = 0
    take_profit_2: float = 0
    trailing_stop: float = 0
    position_size_pct: float = 0
    opened_at: float = 0
    regime_at_entry: str = ""
    tp1_hit: bool = False
    original_quantity: float = 0
    status: str = "OPEN"  # OPEN, CLOSED, PARTIAL
    close_reason: str = ""
    closed_at: float = 0
    pnl: float = 0
    pnl_pct: float = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.opened_at:
            self.opened_at = time.time()
        if not self.original_quantity:
            self.original_quantity = self.quantity


@dataclass
class Trade:
    """Completed trade record."""
    id: str = ""
    symbol: str = ""
    action: str = ""
    entry_price: float = 0
    exit_price: float = 0
    quantity: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    opened_at: float = 0
    closed_at: float = 0
    close_reason: str = ""
    holding_days: float = 0


class PaperTradingEngine:
    """
    Paper trading simulation engine.
    - Virtual portfolio management
    - Real-time position monitoring with auto-exits
    - Performance analytics (Sharpe, Max Drawdown, Win Rate)
    """

    def __init__(self, initial_balance: float = None, portfolio_id: str = None):
        self.portfolio_id = portfolio_id or str(uuid.uuid4())[:12]
        self.initial_balance = initial_balance or settings.DEFAULT_VIRTUAL_BALANCE
        self.cash = self.initial_balance
        self.positions: dict[str, Position] = {}
        self.trade_history: list[Trade] = []
        self.equity_curve: list[dict] = []
        self._created_at = time.time()

    # ── Portfolio Info ──────────────────────────────────────────

    def get_portfolio(self) -> dict:
        """Get current portfolio state."""
        positions_value = sum(
            p.current_price * p.quantity for p in self.positions.values() if p.status == "OPEN"
        )
        total_equity = self.cash + positions_value
        total_pnl = total_equity - self.initial_balance

        return {
            "portfolioId": self.portfolio_id,
            "initialBalance": round(self.initial_balance, 2),
            "cash": round(self.cash, 2),
            "positionsValue": round(positions_value, 2),
            "totalEquity": round(total_equity, 2),
            "totalPnl": round(total_pnl, 2),
            "totalPnlPct": round(total_pnl / self.initial_balance * 100, 2),
            "openPositions": len([p for p in self.positions.values() if p.status == "OPEN"]),
            "totalTrades": len(self.trade_history),
            "winRate": self._compute_win_rate(),
            "sharpeRatio": self._compute_sharpe(),
            "maxDrawdown": self._compute_max_drawdown(),
        }

    def get_positions(self) -> list[dict]:
        """Get all open positions."""
        return [
            {
                "id": p.id,
                "symbol": p.symbol,
                "action": p.action,
                "entryPrice": round(p.entry_price, 2),
                "currentPrice": round(p.current_price, 2),
                "quantity": round(p.quantity, 4),
                "pnl": round(p.pnl, 2),
                "pnlPct": round(p.pnl_pct, 2),
                "stopLoss": round(p.stop_loss, 2),
                "takeProfit1": round(p.take_profit_1, 2),
                "takeProfit2": round(p.take_profit_2, 2),
                "trailingStop": round(p.trailing_stop, 2),
                "tp1Hit": p.tp1_hit,
                "status": p.status,
                "holdingDays": round((time.time() - p.opened_at) / 86400, 1),
                "regime": p.regime_at_entry,
            }
            for p in self.positions.values() if p.status == "OPEN"
        ]

    def get_trade_history(self) -> list[dict]:
        """Get completed trade history."""
        return [asdict(t) for t in self.trade_history[-50:]]  # Last 50

    # ── Trade Execution ─────────────────────────────────────────

    def open_position(
        self,
        symbol: str,
        action: str,
        price: float,
        position_size_pct: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: float,
        regime: str = "",
    ) -> dict:
        """Open a new paper trading position."""
        # Check if position already exists for this symbol
        existing = [p for p in self.positions.values() if p.symbol == symbol and p.status == "OPEN"]
        if existing:
            return {"error": f"Position already open for {symbol}", "position_id": existing[0].id}

        # Calculate position size
        total_equity = self.cash + sum(p.current_price * p.quantity for p in self.positions.values() if p.status == "OPEN")
        allocation = total_equity * (position_size_pct / 100)

        # Slippage
        slippage = price * settings.DEFAULT_SLIPPAGE
        fill_price = price + slippage if action == "BUY" else price - slippage

        quantity = allocation / fill_price
        cost = quantity * fill_price

        if cost > self.cash:
            return {"error": "Insufficient cash", "available": round(self.cash, 2), "required": round(cost, 2)}

        self.cash -= cost

        pos = Position(
            symbol=symbol,
            action=action,
            entry_price=fill_price,
            current_price=fill_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            trailing_stop=stop_loss,
            position_size_pct=position_size_pct,
            regime_at_entry=regime,
        )

        self.positions[pos.id] = pos
        logger.info(f"Opened {action} position: {symbol} @ {fill_price:.2f}, qty={quantity:.4f}")

        return {
            "success": True,
            "positionId": pos.id,
            "symbol": symbol,
            "action": action,
            "fillPrice": round(fill_price, 2),
            "quantity": round(quantity, 4),
            "cost": round(cost, 2),
        }

    def close_position(self, position_id: str, price: float, reason: str = "MANUAL") -> dict:
        """Close a position."""
        pos = self.positions.get(position_id)
        if not pos or pos.status != "OPEN":
            return {"error": "Position not found or already closed"}

        # Slippage
        slippage = price * settings.DEFAULT_SLIPPAGE
        fill_price = price - slippage if pos.action == "BUY" else price + slippage

        # Calculate P&L
        if pos.action == "BUY":
            pnl = (fill_price - pos.entry_price) * pos.quantity
        else:
            pnl = (pos.entry_price - fill_price) * pos.quantity

        pnl_pct = (pnl / (pos.entry_price * pos.quantity)) * 100

        # Update cash
        proceeds = fill_price * pos.quantity
        self.cash += proceeds

        # Close position
        pos.status = "CLOSED"
        pos.close_reason = reason
        pos.closed_at = time.time()
        pos.pnl = pnl
        pos.pnl_pct = pnl_pct
        pos.current_price = fill_price

        # Record trade
        trade = Trade(
            id=pos.id,
            symbol=pos.symbol,
            action=pos.action,
            entry_price=pos.entry_price,
            exit_price=fill_price,
            quantity=pos.original_quantity,
            pnl=pnl,
            pnl_pct=pnl_pct,
            opened_at=pos.opened_at,
            closed_at=pos.closed_at,
            close_reason=reason,
            holding_days=(pos.closed_at - pos.opened_at) / 86400,
        )
        self.trade_history.append(trade)

        logger.info(f"Closed {pos.symbol} ({reason}): PnL={pnl:.2f} ({pnl_pct:.1f}%)")

        return {
            "success": True,
            "symbol": pos.symbol,
            "exitPrice": round(fill_price, 2),
            "pnl": round(pnl, 2),
            "pnlPct": round(pnl_pct, 2),
            "reason": reason,
        }

    # ── Auto-Exit Monitoring ────────────────────────────────────

    def check_auto_exits(self, current_prices: dict[str, float], regime: str = "", panic_score: float = 0) -> list[dict]:
        """Check all open positions for auto-exit conditions."""
        exits = []

        for pos in list(self.positions.values()):
            if pos.status != "OPEN":
                continue

            price = current_prices.get(pos.symbol, pos.current_price)
            pos.current_price = price

            # Update P&L
            if pos.action == "BUY":
                pos.pnl = (price - pos.entry_price) * pos.quantity
            else:
                pos.pnl = (pos.entry_price - price) * pos.quantity
            pos.pnl_pct = (pos.pnl / (pos.entry_price * pos.quantity)) * 100

            exit_reason = None

            # 1. STOP LOSS HIT
            if pos.action == "BUY" and price <= pos.trailing_stop:
                exit_reason = "STOP_LOSS"
            elif pos.action == "SELL" and price >= pos.trailing_stop:
                exit_reason = "STOP_LOSS"

            # 2. TAKE PROFIT SEQUENCE
            if not exit_reason and not pos.tp1_hit:
                if pos.action == "BUY" and price >= pos.take_profit_1:
                    # TP1: Exit 50%, move stop to breakeven
                    half = pos.quantity / 2
                    result = self._partial_close(pos, price, half, "TP1_HIT")
                    exits.append(result)
                    pos.tp1_hit = True
                    pos.trailing_stop = pos.entry_price  # Breakeven
                    continue
                elif pos.action == "SELL" and price <= pos.take_profit_1:
                    half = pos.quantity / 2
                    result = self._partial_close(pos, price, half, "TP1_HIT")
                    exits.append(result)
                    pos.tp1_hit = True
                    pos.trailing_stop = pos.entry_price
                    continue

            if not exit_reason and pos.tp1_hit:
                if pos.action == "BUY" and price >= pos.take_profit_2:
                    exit_reason = "TP2_HIT"
                elif pos.action == "SELL" and price <= pos.take_profit_2:
                    exit_reason = "TP2_HIT"

            # 3. TRAILING STOP ADVANCEMENT (after TP1)
            if pos.tp1_hit and not exit_reason:
                atr_est = pos.entry_price * 0.015
                if pos.action == "BUY":
                    new_trail = price - 0.75 * atr_est
                    if new_trail > pos.trailing_stop:
                        pos.trailing_stop = new_trail
                else:
                    new_trail = price + 0.75 * atr_est
                    if new_trail < pos.trailing_stop:
                        pos.trailing_stop = new_trail

            # 4. REGIME FLIP
            if not exit_reason and regime:
                if pos.action == "BUY" and regime in ("BEAR_TRENDING", "HIGH_VOL_CRISIS"):
                    if pos.regime_at_entry in ("BULL_TRENDING", "LOW_VOL_RANGE"):
                        exit_reason = "REGIME_FLIP"

            # 5. PANIC SPIKE
            if not exit_reason and panic_score > settings.PANIC_EXIT_THRESHOLD:
                exit_reason = "PANIC_SPIKE"

            # 6. TIME STOP
            if not exit_reason:
                holding_days = (time.time() - pos.opened_at) / 86400
                if holding_days > settings.TIME_STOP_DAYS and pos.pnl_pct < 1.0:
                    exit_reason = "TIME_STOP"

            # Execute exit
            if exit_reason:
                result = self.close_position(pos.id, price, exit_reason)
                exits.append(result)

        # Record equity
        self._record_equity()
        return exits

    def _partial_close(self, pos: Position, price: float, quantity: float, reason: str) -> dict:
        """Partially close a position."""
        pnl = (price - pos.entry_price) * quantity if pos.action == "BUY" else (pos.entry_price - price) * quantity
        proceeds = price * quantity
        self.cash += proceeds
        pos.quantity -= quantity

        trade = Trade(
            id=f"{pos.id}_partial",
            symbol=pos.symbol,
            action=pos.action,
            entry_price=pos.entry_price,
            exit_price=price,
            quantity=quantity,
            pnl=pnl,
            pnl_pct=(pnl / (pos.entry_price * quantity)) * 100,
            opened_at=pos.opened_at,
            closed_at=time.time(),
            close_reason=reason,
            holding_days=(time.time() - pos.opened_at) / 86400,
        )
        self.trade_history.append(trade)

        return {
            "success": True,
            "symbol": pos.symbol,
            "exitPrice": round(price, 2),
            "quantity": round(quantity, 4),
            "pnl": round(pnl, 2),
            "reason": reason,
            "partial": True,
        }

    # ── Performance Analytics ───────────────────────────────────

    def _record_equity(self):
        """Record current equity for curve tracking."""
        total = self.cash + sum(p.current_price * p.quantity for p in self.positions.values() if p.status == "OPEN")
        self.equity_curve.append({"timestamp": time.time(), "equity": round(total, 2)})
        # Keep last 1000 points
        if len(self.equity_curve) > 1000:
            self.equity_curve = self.equity_curve[-1000:]

    def _compute_win_rate(self) -> float:
        if not self.trade_history:
            return 0
        wins = sum(1 for t in self.trade_history if t.pnl > 0)
        return round(wins / len(self.trade_history) * 100, 1)

    def _compute_sharpe(self) -> float:
        if len(self.equity_curve) < 10:
            return 0
        equities = [e["equity"] for e in self.equity_curve]
        returns = np.diff(equities) / equities[:-1]
        if len(returns) < 2 or np.std(returns) == 0:
            return 0
        return round(float(np.mean(returns) / np.std(returns) * np.sqrt(252)), 2)

    def _compute_max_drawdown(self) -> float:
        if len(self.equity_curve) < 2:
            return 0
        equities = np.array([e["equity"] for e in self.equity_curve])
        peak = np.maximum.accumulate(equities)
        dd = (equities - peak) / peak * 100
        return round(float(np.min(dd)), 2)

    def get_performance(self) -> dict:
        """Detailed performance analytics."""
        portfolio = self.get_portfolio()
        if not self.trade_history:
            return {**portfolio, "avgWin": 0, "avgLoss": 0, "avgRR": 0, "profitFactor": 0}

        wins = [t for t in self.trade_history if t.pnl > 0]
        losses = [t for t in self.trade_history if t.pnl <= 0]

        avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t.pnl for t in losses) / len(losses)) if losses else 0
        profit_factor = sum(t.pnl for t in wins) / max(abs(sum(t.pnl for t in losses)), 1) if losses else float('inf')

        return {
            **portfolio,
            "avgWin": round(avg_win, 2),
            "avgLoss": round(avg_loss, 2),
            "avgHoldingDays": round(sum(t.holding_days for t in self.trade_history) / len(self.trade_history), 1),
            "profitFactor": round(profit_factor, 2),
            "equityCurve": self.equity_curve[-100:],  # Last 100 points
        }

    # ── Persistence ─────────────────────────────────────────────

    def save(self, path: Path = None):
        """Save portfolio state to disk."""
        if path is None:
            path = settings.DATA_DIR / f"portfolio_{self.portfolio_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "portfolioId": self.portfolio_id,
            "initialBalance": self.initial_balance,
            "cash": self.cash,
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "tradeHistory": [asdict(t) for t in self.trade_history],
            "equityCurve": self.equity_curve,
            "createdAt": self._created_at,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, portfolio_id: str) -> Optional["PaperTradingEngine"]:
        """Load portfolio from disk."""
        path = settings.DATA_DIR / f"portfolio_{portfolio_id}.json"
        if not path.exists():
            return None

        with open(path) as f:
            data = json.load(f)

        engine = cls(data["initialBalance"], data["portfolioId"])
        engine.cash = data["cash"]
        engine._created_at = data.get("createdAt", time.time())
        engine.equity_curve = data.get("equityCurve", [])

        for pid, pdata in data.get("positions", {}).items():
            engine.positions[pid] = Position(**pdata)

        for tdata in data.get("tradeHistory", []):
            engine.trade_history.append(Trade(**tdata))

        return engine


# Portfolio registry
_portfolios: dict[str, PaperTradingEngine] = {}


def get_or_create_portfolio(portfolio_id: str = None, initial_balance: float = None) -> PaperTradingEngine:
    global _portfolios
    if portfolio_id and portfolio_id in _portfolios:
        return _portfolios[portfolio_id]

    # Try loading from disk
    if portfolio_id:
        engine = PaperTradingEngine.load(portfolio_id)
        if engine:
            _portfolios[portfolio_id] = engine
            return engine

    engine = PaperTradingEngine(initial_balance=initial_balance, portfolio_id=portfolio_id)
    _portfolios[engine.portfolio_id] = engine
    return engine
