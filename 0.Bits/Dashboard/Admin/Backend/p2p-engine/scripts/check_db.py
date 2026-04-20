import sqlite3

db = sqlite3.connect("/data/PearV2/data/cop_orders.db")

cols = [c[1] for c in db.execute("PRAGMA table_info(cop_orders)")]

print("=== Orders in generating_link or info_received with complete info ===")
for row in db.execute("SELECT * FROM cop_orders WHERE state IN ('generating_link', 'info_received', 'awaiting_info') ORDER BY created_at DESC"):
    d = dict(zip(cols, row))
    print(f"  ORDER: {d['binance_order_id']}")
    print(f"    state={d['state']} | name={d.get('customer_name','')} | cc={d.get('customer_cc','')} | email={d.get('customer_email','')} | bank={d.get('bank_code','')}")
    print(f"    COP={d.get('amount_cop','')} | USDT={d.get('amount_usdt','')}")
    has_info = d.get('customer_cc') and d.get('customer_email') and d.get('bank_code')
    print(f"    complete_info={has_info}")

# Reset generating_link to info_received so they retry with auto_send
c = db.execute("UPDATE cop_orders SET state='info_received' WHERE state='generating_link'")
print(f"\nReset {c.rowcount} generating_link orders to info_received")

# Also check for link_sent orders
for row in db.execute("SELECT * FROM cop_orders WHERE state = 'link_sent'"):
    d = dict(zip(cols, row))
    print(f"  LINK_SENT: {d['binance_order_id']}")

db.commit()
db.close()
