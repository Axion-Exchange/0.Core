"""Check FP transaction status via direct API call"""
import asyncio, os, sys
sys.path.insert(0, "/data/PearV2")
from dotenv import load_dotenv
load_dotenv("/data/PearV2/.env")
import httpx

TX_ID_261K = "b8d2e677-ab53-454e-be5e-99a744baa2f3"  # 261K order

async def main():
    # Auth
    async with httpx.AsyncClient(timeout=30.0) as client:
        auth_resp = await client.post("https://api.facilitapay.com/api/v1/auth/jwt", json={
            "email": os.getenv("FACILITAPAY_USERNAME"),
            "password": os.getenv("FACILITAPAY_PASSWORD"),
        })
        token = auth_resp.json().get("jwt")
        print(f"Auth: {'OK' if token else 'FAILED'}")

        # Get transaction
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(f"https://api.facilitapay.com/api/v1/transactions/{TX_ID_261K}", headers=headers)
        data = resp.json()
        if "data" in data:
            d = data["data"]
            print(f"Status: {d.get('status')}")
            print(f"Value: {d.get('value')}")
            print(f"PSE info: {d.get('pse_info', d.get('from_pse', {}))}")
        else:
            print(f"Response: {data}")

asyncio.run(main())
