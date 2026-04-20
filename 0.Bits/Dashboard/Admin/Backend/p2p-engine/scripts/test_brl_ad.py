"""Test creating a BRL sell ad on Binance P2P"""
import hmac, hashlib, time, os, requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv("/data/PearV2/.env")

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BASE = "https://api.binance.com"

def signed_request(method, path, params=None):
    params = params or {}
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = 10000
    query = urlencode(params)
    sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    query += f"&signature={sig}"
    url = f"{BASE}{path}?{query}"
    headers = {"X-MBX-APIKEY": API_KEY}
    if method == "GET":
        r = requests.get(url, headers=headers, timeout=10)
    else:
        r = requests.post(url, headers=headers, timeout=10)
    return r

# First, try to list existing ads to see if the endpoint works
print("=== Testing: List existing ads ===")
r = signed_request("POST", "/sapi/v1/c2c/ads/getList")
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

# Try to get ad detail / search
print("\n=== Testing: Search BRL market ===")
r2 = requests.post(
    "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search",
    json={"fiat": "BRL", "asset": "USDT", "tradeType": "SELL", "page": 1, "rows": 3},
    headers={"Content-Type": "application/json"},
    timeout=10,
)
print(f"Status: {r2.status_code}")
data = r2.json()
if data.get("data"):
    for ad in data["data"][:3]:
        adv = ad.get("adv", {})
        print(f"  Price: {adv.get('price')} BRL | Min: {adv.get('minSingleTransAmount')} | Max: {adv.get('maxSingleTransAmount')}")

# Now try creating a test BRL sell ad
print("\n=== Testing: Create BRL sell ad (100 USDT) ===")
ad_params = {
    "asset": "USDT",
    "fiatUnit": "BRL",
    "tradeType": "SELL",
    "priceType": "FLOATING",
    "priceFloatingRatio": "1.02",  # 2% above market
    "totalAmount": "100",
    "minAmount": "50",
    "maxAmount": "1000",
    "payTypes": "PIX",
    "autoReplyMsg": "Test ad - please proceed with payment",
}
r3 = signed_request("POST", "/sapi/v1/c2c/ads/post", ad_params)
print(f"Status: {r3.status_code}")
print(f"Response: {r3.text[:500]}")
