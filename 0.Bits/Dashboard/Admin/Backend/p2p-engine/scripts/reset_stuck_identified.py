"""Reset stuck COP orders from manual_review to link_sent so they get retried."""
import sqlite3

conn = sqlite3.connect("data/cop_orders.db")
conn.row_factory = sqlite3.Row

# Find orders that were identified but failed due to state transition rejection
rows = conn.execute("""
    SELECT binance_order_id, state, amount_cop, amount_usdt, facilitapay_tx_id
    FROM cop_orders
    WHERE state = 'manual_review' AND facilitapay_tx_id IS NOT NULL
""").fetchall()

print(f"Found {len(rows)} manual_review orders with FP tx IDs:")
for r in rows:
    print(f"  {r['binance_order_id']} | COP={r['amount_cop']} | USDT={r['amount_usdt']} | fp_tx={r['facilitapay_tx_id'][:12]}...")

# Reset them back to link_sent, and clear any release claims
for r in rows:
    oid = r['binance_order_id']
    conn.execute("UPDATE cop_orders SET state = 'link_sent' WHERE binance_order_id = ?", (oid,))
    conn.execute("DELETE FROM cop_releases WHERE order_id = ?", (oid,))
    print(f"  -> Reset {oid} to link_sent + cleared release guard")

conn.commit()
conn.close()
print(f"\nDone! Poll cycle will retry {len(rows)} orders within ~30 seconds.")
