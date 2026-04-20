"""Check Binance order status for the stuck COP orders."""
import asyncio, sys
sys.path.insert(0, "/data/PearV2")
from dotenv import load_dotenv
load_dotenv("/data/PearV2/.env")
import os
from src.fiat.cop.binance_chat import BinanceChatClient

# Orders that got 400 on release
ORDERS = [
    "22856397089881890816",
    "22856390616771092480", 
    "22856388287714529280",
    "22856388428607840256",
]

async def main():
    api_key = os.environ.get("BINANCE_COP_API_KEY") or os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_COP_API_SECRET") or os.environ.get("BINANCE_API_SECRET")
    client = BinanceChatClient(api_key, api_secret)
    
    for oid in ORDERS:
        detail = await client.get_order_detail(oid)
        if detail:
            status = detail.get("orderStatus")
            trade_amount = detail.get("amount")
            total_price = detail.get("totalPrice")
            print(f"{oid}: status={status} amount={trade_amount} price={total_price}")
        else:
            print(f"{oid}: NOT FOUND (404)")
    
    # Also try the actual release response for debugging
    print("\n--- Try release on first order to see error body ---")
    import httpx
    body = {"orderNumber": ORDERS[0]}
    try:
        auth_params = client._sign({})
        import urllib.parse
        query = urllib.parse.urlencode(auth_params)
        resp = await client.client.post(f"/sapi/v1/c2c/orderMatch/releaseCoin?{query}", json=body)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    await client.close()

asyncio.run(main())
