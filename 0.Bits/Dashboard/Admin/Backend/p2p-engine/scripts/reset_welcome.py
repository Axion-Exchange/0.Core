#!/usr/bin/env python3
"""Reset welcome_sent flag for stuck COP order."""
import sqlite3
c = sqlite3.connect("data/cop_orders.db")
c.execute("UPDATE cop_orders SET welcome_sent=0 WHERE binance_order_id='22855366778889428992'")
c.commit()
print("Reset welcome_sent to 0 for order 22855366778889428992")
# Verify
r = c.execute("SELECT welcome_sent FROM cop_orders WHERE binance_order_id='22855366778889428992'").fetchone()
print(f"Verified: welcome_sent = {r[0]}")
