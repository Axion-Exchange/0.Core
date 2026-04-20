"""One-shot: mark old Binance-404 orders as completed/cancelled in COP DB."""
import sqlite3

STALE_IDENTIFIED = [
    "22856397089881890816",
    "22856390616771092480",
    "22856388287714529280",
    "22856388428607840256",
    "22856386988871761920",
    "22856382563209539584",
    "22856382312995991552",
    "22856378046195154944",
]

STALE_CANCELLED = [
    "22856396044820656128",
    "22856396339547049984",
    "22856392020769353728",
    "22856390987078307840",
    "22856388965493428224",
    "22856388108418920448",
    "22856387421916213248",
    "22856384604788613120",
    "22856380537817460736",
    "22856182260500258816",
    "22856398335924494336",
    "22856398626441506816",
    "22856398028230938624",
    "22856855832628933804032",
]

conn = sqlite3.connect("data/cop_orders.db")
for oid in STALE_IDENTIFIED:
    cur = conn.execute("UPDATE cop_orders SET state='completed' WHERE binance_order_id=? AND state='link_sent'", (oid,))
    if cur.rowcount:
        print(f"COMPLETED: {oid}")
for oid in STALE_CANCELLED:
    cur = conn.execute("UPDATE cop_orders SET state='cancelled' WHERE binance_order_id=? AND state='link_sent'", (oid,))
    if cur.rowcount:
        print(f"CANCELLED: {oid}")

conn.commit()
conn.close()
print("Done")
