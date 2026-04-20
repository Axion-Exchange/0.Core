"""Send the existing PSE link to the customer who never received it"""
import asyncio, os, sqlite3, sys
sys.path.insert(0, "/data/PearV2")
from dotenv import load_dotenv
load_dotenv("/data/PearV2/.env")

from src.fiat.cop.binance_chat import BinanceChatClient

ORDER_ID = "22855443550657003520"

# Get the payment URL from FP DB
db = sqlite3.connect("/data/PearV2/data/facilitapay.db")
row = db.execute("SELECT payment_url FROM fp_transactions WHERE pear_order_id=?", (ORDER_ID,)).fetchone()
if not row or not row[0]:
    print(f"ERROR: No payment URL found for {ORDER_ID}")
    sys.exit(1)

payment_url = row[0]
print(f"Found URL: {payment_url}")

# Send via Binance chat
client = BinanceChatClient(
    os.getenv("BINANCE_API_KEY"),
    os.getenv("BINANCE_API_SECRET"),
)

msg = f"💳 Tu enlace de pago PSE está listo:\n\n{payment_url}\n\nPor favor completa el pago a través de tu banco."

async def main():
    ok = await client.send_chat_message(ORDER_ID, msg)
    if ok:
        print(f"✅ PSE link sent to {ORDER_ID}")
        # Update order state to link_sent
        db2 = sqlite3.connect("/data/PearV2/data/cop_orders.db")
        db2.execute("UPDATE cop_orders SET state='link_sent' WHERE binance_order_id=?", (ORDER_ID,))
        db2.commit()
        db2.close()
        print("✅ Order state updated to link_sent")
    else:
        print("❌ Failed to send message")

asyncio.run(main())
db.close()
