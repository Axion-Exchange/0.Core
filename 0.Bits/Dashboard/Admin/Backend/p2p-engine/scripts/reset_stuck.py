import sqlite3

db = sqlite3.connect("/data/PearV2/data/cop_orders.db")

# Reset Josefa's order and the other stuck one from manual_review to info_received
orders_to_reset = ['22855431886926725120', '22855431837833486336']
for oid in orders_to_reset:
    db.execute("UPDATE cop_orders SET state='info_received' WHERE binance_order_id=?", (oid,))
    print(f"Reset {oid} to info_received")

db.commit()

# Verify
for row in db.execute("SELECT binance_order_id, state, customer_cc, bank_code FROM cop_orders"):
    print(f"  {row}")

db.close()
