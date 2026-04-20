"""Show all COP orders from today."""
import sqlite3

conn = sqlite3.connect("data/cop_orders.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT binance_order_id, state, amount_cop, amount_usdt, binance_buyer_name, created_at
    FROM cop_orders
    WHERE created_at >= '2026-02-15'
    ORDER BY created_at
""")
rows = cur.fetchall()

states = {}
total_cop = 0
completed_cop = 0
cancelled_cop = 0

for r in rows:
    s = r["state"]
    states[s] = states.get(s, 0) + 1
    try:
        cop = float(r["amount_cop"] or 0)
        total_cop += cop
        if s == "completed":
            completed_cop += cop
        elif s == "cancelled":
            cancelled_cop += cop
    except Exception:
        pass

print(f"=== COP Orders Today (Feb 15, 2026) ===")
print(f"Total opened: {len(rows)}")
print(f"Total COP volume: {total_cop:,.0f} COP")
print()
print("By status:")
for s, c in sorted(states.items()):
    print(f"  {s}: {c}")
print()
print(f"Completed volume: {completed_cop:,.0f} COP")
print(f"Cancelled volume: {cancelled_cop:,.0f} COP")
print()
print("--- Individual Orders ---")
print(f"{'Order ID':>14s} | {'State':20s} | {'COP':>12s} | {'USDT':>8s} | {'Buyer':25s} | Created")
print("-" * 120)
for r in rows:
    oid = r["binance_order_id"][-14:]
    cop = float(r["amount_cop"] or 0)
    usdt = float(r["amount_usdt"] or 0)
    name = (r["binance_buyer_name"] or "")[:25]
    print(f"{oid:>14s} | {r['state']:20s} | {cop:>12,.0f} | {usdt:>8.2f} | {name:25s} | {r['created_at']}")

conn.close()
