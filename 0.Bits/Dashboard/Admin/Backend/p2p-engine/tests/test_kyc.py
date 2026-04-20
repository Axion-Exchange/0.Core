import asyncio
import os
from dotenv import load_dotenv
from src.exchanges.binance.api_translator import BinanceApiTranslator

load_dotenv()

async def main():
    api_key = os.getenv('BINANCE_API_KEY', '')
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    
    translator = BinanceApiTranslator(api_key, api_secret)
    
    order_id = '22850328786605092864'
    print(f"Testing verify_identity for order {order_id}...")
    
    result = await translator.verify_identity(order_id)
    
    if result:
        print("\n[SUCCESS] Verification request sent successfully!")
    else:
        print("\n[FAILED] Verification request failed.")

asyncio.run(main())
