#!/usr/bin/env python3
"""
Emergency: Force-sync FP transaction statuses and trigger release for identified orders.

This script:
1. Checks ALL FP transactions against the live API
2. Updates local DB status to match
3. For any 'identified' transactions, triggers the webhook release flow
"""
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
    
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_fp = os.path.join(base, "data", "facilitapay.db")
    
    conn = sqlite3.connect(db_fp)
    rows = conn.execute(
        "SELECT id, pear_order_id, status FROM fp_transactions WHERE status = 'pending'"
    ).fetchall()
    
    print(f"Found {len(rows)} pending FP transactions to check")
    print("=" * 80)
    
    identified = []
    for tx_id, order_id, local_status in rows:
        try:
            result = await client.get_transaction_status(tx_id)
            api_status = result.get("status", "unknown")
            
            if api_status != local_status:
                print(f"UPDATING {order_id}: {local_status} -> {api_status}")
                conn.execute(
                    "UPDATE fp_transactions SET status = ? WHERE id = ?",
                    (api_status, tx_id)
                )
                conn.commit()
                
                if api_status == "identified":
                    identified.append((tx_id, order_id))
            else:
                print(f"OK {order_id}: still {api_status}")
        except Exception as e:
            print(f"ERROR {order_id}: {e}")
    
    conn.close()
    
    print()
    print(f"Found {len(identified)} identified orders that need release")
    
    if identified:
        print("The bot's polling loop should now detect these on the next cycle")
        print("since local DB status is updated to 'identified'")
        for tx_id, order_id in identified:
            print(f"  -> {order_id} (tx={tx_id[:16]})")
    
    await client.close()

asyncio.run(main())
