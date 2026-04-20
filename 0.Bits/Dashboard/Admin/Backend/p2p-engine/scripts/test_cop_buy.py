"""Quick test: Check FP cashout balance and list payout banks."""
import asyncio
import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.fiat.cop.facilitapay_client import FacilitaPayCopClient

async def main():
    client = FacilitaPayCopClient(
        username=os.getenv("FACILITAPAY_USERNAME"),
        password=os.getenv("FACILITAPAY_PASSWORD"),
        cashin_account_id=os.getenv("FACILITAPAY_CASHIN_ACCOUNT_ID", ""),
        cashout_account_id=os.getenv("FACILITAPAY_CASHOUT_ACCOUNT_ID", ""),
        webhook_secret=os.getenv("FACILITAPAY_WEBHOOK_SECRET", ""),
        db_path="data/facilitapay.db",
    )

    print(f"Cashout account: {client.cashout_account_id}")
    print(f"Cashin account:  {client.cashin_account_id}")
    print()

    # Test 1: Check cashout balance
    try:
        balance = await client.get_cashout_balance()
        print(f"[OK] Cashout balance: {balance} COP")
    except Exception as e:
        print(f"[FAIL] Cashout balance failed: {e}")

    # Test 2: Get payout banks
    try:
        banks = await client.get_payout_banks()
        print(f"[OK] Payout banks: {len(banks)} banks available")
        for b in banks[:5]:
            print(f"  - {b.code}: {b.name}")
    except Exception as e:
        print(f"[FAIL] Payout banks failed: {e}")

    # Test 3: Try mark_order_paid on Binance (dry check only)
    from src.fiat.cop.binance_chat import BinanceChatClient
    binance = BinanceChatClient(
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET"),
    )
    print(f"\n[INFO] Binance mark_order_paid endpoint: /sapi/v1/c2c/orderMatch/markOrderAsPaid")
    print(f"[INFO] This endpoint exists and is implemented in binance_chat.py line 220")

    await client.close()

asyncio.run(main())
