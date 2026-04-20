import requests, json

fiats = [
    "EUR","GBP","USD","CAD","AUD","CHF","SEK","NOK","DKK","PLN","CZK","HUF","RON","BGN","HRK",
    "TRY","RUB","UAH","KZT","GEL","AZN","UZS",
    "COP","BRL","ARS","MXN","PEN","CLP","BOB","VES","PYG","UYU","DOP","CRC","GTQ","HNL","NIO","PAB",
    "NGN","KES","GHS","ZAR","EGP","MAD","TZS","UGX","XOF","XAF",
    "INR","PKR","BDT","LKR","NPR","PHP","VND","THB","IDR","MYR","SGD","HKD","JPY","KRW","TWD","CNY",
    "AED","SAR","QAR","BHD","KWD","OMR","JOD","ILS",
]

print(f"Checking {len(fiats)} currencies...\n")
available = []

for fiat in fiats:
    try:
        resp = requests.post(
            "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search",
            json={"fiat": fiat, "asset": "USDT", "tradeType": "SELL", "page": 1, "rows": 1},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        data = resp.json()
        ads = data.get("data", [])
        total = data.get("total", 0)
        if ads or total > 0:
            price = ads[0].get("adv", {}).get("price", "?") if ads else "?"
            available.append((fiat, total, price))
    except Exception as e:
        pass

print(f"{'FIAT':<6} {'ADS':>6}  {'BEST PRICE':>12}")
print("-" * 28)
for fiat, total, price in sorted(available, key=lambda x: -x[1]):
    print(f"{fiat:<6} {total:>6}  {price:>12}")
print(f"\nTotal: {len(available)} currencies with active USDT sell ads")
