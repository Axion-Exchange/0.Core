"""Check for COP orders that are identified but not released."""
import sqlite3

conn = sqlite3.connect("data/cop_orders.db")
conn.row_factory = sqlite3.Row

print("=== All non-terminal COP orders ===")
rows = conn.execute("""
    SELECT binance_order_id, state, amount_cop, amount_usdt, order_side, created_at 
    FROM cop_orders 
    WHERE state NOT IN ('completed', 'cancelled')
    ORDER BY created_at DESC
""").fetchall()
for r in rows:
    print(f"  {r['binance_order_id']} | {r['state']:20s} | COP={r['amount_cop']} | USDT={r['amount_usdt']} | side={r['order_side'] or 'SELL'} | {r['created_at']}")

print(f"\nTotal non-terminal: {len(rows)}")

print("\n=== Orders in link_sent state (should be checking for payment) ===")
link_sent = conn.execute("""
    SELECT binance_order_id, state, amount_cop, amount_usdt, facilitapay_tx_id, created_at
    FROM cop_orders 
    WHERE state = 'link_sent'
    ORDER BY created_at DESC
""").fetchall()
for r in link_sent:
    print(f"  {r['binance_order_id']} | COP={r['amount_cop']} | fp_tx={r['facilitapay_tx_id'] or 'NONE'} | {r['created_at']}")

print(f"\nTotal link_sent: {len(link_sent)}")

print("\n=== Recent audit log entries ===")
recent = conn.execute("""
    SELECT order_id, event, details, result, timestamp 
    FROM audit_log 
    WHERE timestamp > datetime('now', '-30 minutes')
    ORDER BY timestamp DESC
    LIMIT 20
""").fetchall()
for r in recent:
    print(f"  {r['timestamp'][:19]} | {r['order_id'][-6:]} | {r['event']:30s} | {r['result'] or ''} | {r['details'][:80] if r['details'] else ''}")

conn.close()
