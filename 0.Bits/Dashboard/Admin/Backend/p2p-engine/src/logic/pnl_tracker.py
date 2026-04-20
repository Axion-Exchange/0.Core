"""
PNL TRACKER
===========
Tracks profit and loss across all P2P trades.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.core.types import UnifiedOrder, UnifiedPayment


class Trade(BaseModel):
    """A completed P2P trade with P&L calculation."""
    order_id: str
    exchange: str
    side: str  # buy or sell
    
    crypto_asset: str
    crypto_amount: float
    
    fiat_currency: str
    fiat_amount: float
    
    # Our effective rate vs market
    our_rate: float
    market_rate: float | None = None
    
    # Calculated profit
    gross_profit: float = 0.0
    fees: float = 0.0
    net_profit: float = 0.0
    
    completed_at: datetime


class PnlTracker:
    """
    Track P&L across all trades.
    
    Features:
    - Real-time profit calculation
    - Daily/weekly/monthly summaries
    - Per-exchange breakdown
    - Per-currency breakdown
    """
    
    def __init__(self):
        self.trades: list[Trade] = []
    
    def record_completed_order(
        self,
        order: UnifiedOrder,
        market_rate: float | None = None,
        fees: float = 0.0,
    ) -> Trade:
        """
        Record a completed order and calculate its P&L.
        """
        crypto_amount = float(order.crypto_amount)
        fiat_amount = float(order.fiat_amount)
        our_rate = fiat_amount / crypto_amount if crypto_amount > 0 else 0
        
        # For sells: we profit if our_rate > market_rate
        # For buys: we profit if our_rate < market_rate
        gross_profit = 0.0
        if market_rate and order.side.value == "sell":
            gross_profit = (our_rate - market_rate) * crypto_amount
        elif market_rate and order.side.value == "buy":
            gross_profit = (market_rate - our_rate) * crypto_amount
        
        net_profit = gross_profit - fees
        
        trade = Trade(
            order_id=order.external_id,
            exchange=order.exchange.value,
            side=order.side.value,
            crypto_asset=order.crypto_asset.value,
            crypto_amount=crypto_amount,
            fiat_currency=order.fiat_currency.value,
            fiat_amount=fiat_amount,
            our_rate=our_rate,
            market_rate=market_rate,
            gross_profit=gross_profit,
            fees=fees,
            net_profit=net_profit,
            completed_at=order.updated_at
        )
        
        self.trades.append(trade)
        return trade
    
    def get_summary(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> dict[str, Any]:
        """
        Get P&L summary with optional filters.
        """
        filtered = self.trades
        
        if start_time:
            filtered = [t for t in filtered if t.completed_at >= start_time]
        if end_time:
            filtered = [t for t in filtered if t.completed_at <= end_time]
        if exchange:
            filtered = [t for t in filtered if t.exchange == exchange]
        if currency:
            filtered = [t for t in filtered if t.fiat_currency == currency]
        
        total_volume = sum(t.fiat_amount for t in filtered)
        total_gross = sum(t.gross_profit for t in filtered)
        total_fees = sum(t.fees for t in filtered)
        total_net = sum(t.net_profit for t in filtered)
        
        return {
            "trade_count": len(filtered),
            "total_volume": total_volume,
            "gross_profit": total_gross,
            "total_fees": total_fees,
            "net_profit": total_net,
            "profit_margin_pct": (total_net / total_volume * 100) if total_volume > 0 else 0,
        }
    
    def get_exchange_breakdown(self) -> dict[str, dict[str, Any]]:
        """Get P&L breakdown by exchange."""
        exchanges = set(t.exchange for t in self.trades)
        return {
            ex: self.get_summary(exchange=ex) 
            for ex in exchanges
        }
