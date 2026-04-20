#!/usr/bin/env python3
"""Check COP orders DB state."""
import sqlite3
c = sqlite3.connect("data/cop_orders.db")
c.row_factory = sqlite3.Row

# Tables
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t["name"] for t in tables])

# Orders
rows = c.execute("SELECT * FROM cop_orders").fetchall()
cols = [d[0] for d in c.execute("SELECT * FROM cop_orders").description]
print(f"\nColumns: {cols}")
for r in rows:
    print(dict(r))

# Audit log
print("\n--- AUDIT LOG (last 20) ---")
try:
    for r in c.execute("SELECT * FROM cop_audit ORDER BY rowid DESC LIMIT 20").fetchall():
        print(dict(r))
except:
    print("No audit table")
