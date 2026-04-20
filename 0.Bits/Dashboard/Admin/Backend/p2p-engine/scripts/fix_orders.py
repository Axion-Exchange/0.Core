"""Fix stuck orders: send link to Jessica + check payment status for 261K order"""
import asyncio, os, sys, sqlite3
sys.path.insert(0, "/data/PearV2")
from dotenv import load_dotenv
load_dotenv("/data/PearV2/.env")

from src.fiat.cop.binance_chat import BinanceChatClient
from src.fiat.cop.facilitapay_client import FacilitaPayCopClient

JESSICA_ORDER = "22855452152995368960"
PAID_ORDER = "22855451806589296640"

async def main():
    fp_db = sqlite3.connect("/data/PearV2/data/facilitapay.db")
    cop_db = sqlite3.connect("/data/PearV2/data/cop_orders.db")
    chat = BinanceChatClient(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))

    fp = FacilitaPayCopClient(
        username=os.getenv("FACILITAPAY_USERNAME"),
        password=os.getenv("FACILITAPAY_PASSWORD"),
        cashin_account_id=os.getenv("FACILITAPAY_CASH_IN_ACCOUNT_ID"),
        cashout_account_id=os.getenv("FACILITAPAY_CASHOUT_ACCOUNT_ID"),
        webhook_secret=os.getenv("FACILITAPAY_WEBHOOK_SECRET", ""),
    )

    # 1. Check Jessica's order
    print(f"\n=== Jessica's order {JESSICA_ORDER} ===")
    jessica_tx = fp_db.execute("SELECT id, payment_url, status FROM fp_transactions WHERE pear_order_id=?", (JESSICA_ORDER,)).fetchone()
    if jessica_tx and jessica_tx[1]:
        print(f"  Link EXISTS: {jessica_tx[1]}")
        payment_url = jessica_tx[1]
    else:
        print("  No link - resetting for bot to generate")
        cop_db.execute("UPDATE cop_orders SET state='info_received' WHERE binance_order_id=?", (JESSICA_ORDER,))
        cop_db.commit()
        print("  Reset to info_received")
        payment_url = None

    if payment_url:
        msg = f"💳 Tu enlace de pago PSE está listo:\n\n{payment_url}\n\nPor favor completa el pago a través de tu banco."
        ok = await chat.send_chat_message(JESSICA_ORDER, msg)
        print(f"  {'✅ Link sent!' if ok else '❌ Send failed'}")
        if ok:
            cop_db.execute("UPDATE cop_orders SET state='link_sent' WHERE binance_order_id=?", (JESSICA_ORDER,))
            cop_db.commit()

    # 2. Check 261K payment on FP API
    print(f"\n=== Paid order {PAID_ORDER} ===")
    paid_tx = fp_db.execute("SELECT id, status, amount FROM fp_transactions WHERE pear_order_id=?", (PAID_ORDER,)).fetchone()
    if paid_tx:
        tx_id = paid_tx[0]
        print(f"  Local: status={paid_tx[1]} amount={paid_tx[2]}")
        await fp._ensure_auth()
        resp = await fp.client.get(f"{fp.base_url}/transactions/{tx_id}", headers={"Authorization": f"Bearer {fp.jwt_token}"})
        data = resp.json()
        if "data" in data:
            d = data["data"]
            print(f"  FP API: status={d.get('status')} value={d.get('value')}")
        else:
            print(f"  FP API response: {data}")

    # Also check ALL FP transactions
    print(f"\n=== All FP transactions ===")
    for row in fp_db.execute("SELECT pear_order_id, status, amount, payment_url FROM fp_transactions"):
        print(f"  {row[0]}: status={row[1]} amount={row[2]} url={'present' if row[3] else 'none'}")

    cop_db.close()
    fp_db.close()
    await fp.close()

asyncio.run(main())
