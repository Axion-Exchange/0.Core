#!/usr/bin/env python3
"""Test FacilitaPay API connectivity from VPS - checks transaction statuses."""
import sqlite3
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    from src.fiat.cop.facilitapay_client import FacilitaPayCopClient
    
    client = FacilitaPayCopClient(
        username=os.getenv("FACILITAPAY_USERNAME", ""),
        password=os.getenv("FACILITAPAY_PASSWORD", ""),
        webhook_secret=os.getenv("FACILITAPAY_WEBHOOK_SECRET", ""),
    )
    
    # Get all FP transactions from local DB
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn = sqlite3.connect(os.path.join(base, "data", "facilitapay.db"))
    rows = conn.execute(
        "SELECT id, pear_order_id, status FROM fp_transactions ORDER BY rowid DESC LIMIT 20"
    ).fetchall()
    conn.close()
    
    print(f"Found {len(rows)} FP transactions in local DB")
    print("=" * 100)
    
    for tx_id, order_id, local_status in rows:
        try:
            result = await client.get_transaction_status(tx_id)
            api_status = result.get("status", "unknown")
            match = "OK" if api_status == local_status else "MISMATCH!"
            print(f"{order_id} | local={local_status:<12} | api={api_status:<12} | {match}")
        except Exception as e:
            print(f"{order_id} | local={local_status:<12} | API ERROR: {e}")
    
    await client.close()

asyncio.run(main())
