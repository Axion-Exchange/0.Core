#!/usr/bin/env python3
"""Reset COP order to retry with full traceback."""
import sqlite3
c = sqlite3.connect("data/cop_orders.db")

# Delete the order entirely so it re-processes from scratch
c.execute("DELETE FROM cop_orders WHERE binance_order_id='22855366778889428992'")
c.execute("DELETE FROM seen_messages WHERE order_id='22855366778889428992'")
c.commit()

print("Deleted order 22855366778889428992 - will be re-discovered on next poll")

# Also check FacilitaPay DB for subjects
try:
    fp = sqlite3.connect("data/facilitapay.db")
    fp.row_factory = sqlite3.Row
    subs = fp.execute("SELECT * FROM fp_subjects").fetchall()
    print(f"\nFacilitaPay subjects: {len(subs)}")
    for s in subs:
        print(dict(s))
    txs = fp.execute("SELECT * FROM fp_transactions").fetchall()
    print(f"\nFacilitaPay transactions: {len(txs)}")
    for t in txs:
        print(dict(t))
except Exception as e:
    print(f"FacilitaPay DB error: {e}")
