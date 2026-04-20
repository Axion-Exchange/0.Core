"""Revert: set orders back to link_sent since they are still active on Binance."""
import sqlite3

# These orders are still LIVE on Binance with "Please Release" status
# The get_order_detail API returned 404 erroneously - they are NOT gone
ORDERS_TO_REVERT = [
    "22856397089881890816",
    "22856390616771092480",
    "22856388287714529280",
    "22856388428607840256",
    "22856386988871761920",
    "22856382563209539584",
    "22856382312995991552",
    "22856378046195154944",
]

conn = sqlite3.connect("data/cop_orders.db")
for oid in ORDERS_TO_REVERT:
    cur = conn.execute("UPDATE cop_orders SET state='link_sent' WHERE binance_order_id=? AND state='completed'", (oid,))
    if cur.rowcount:
        print(f"REVERTED to link_sent: {oid}")
    else:
        row = conn.execute("SELECT state FROM cop_orders WHERE binance_order_id=?", (oid,)).fetchone()
        print(f"SKIP {oid} (current state: {row[0] if row else 'NOT FOUND'})")

conn.commit()
conn.close()
print("Done")
