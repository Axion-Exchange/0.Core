"""
Test if we can still contact counterparties on completed orders.
Fetches 90 days of completed orders, attempts to send a test message to each.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.exchanges.binance.api_client import BinanceApiClient
from src.core.types import OrderStatus


async def main():
    client = BinanceApiClient(
        os.getenv("BINANCE_API_KEY"),
        os.getenv("BINANCE_API_SECRET"),
    )

    now = datetime.now(timezone.utc)
    start_ts = int((now - timedelta(days=90)).timestamp() * 1000)
    end_ts = int(now.timestamp() * 1000)

    # Fetch all completed orders (90 days)
    print(">> Fetching 90-day order history...")
    all_orders = []
    for trade_type in ["BUY", "SELL"]:
        page = 1
        while True:
            batch = await client.get_order_history(
                trade_type=trade_type,
                start_timestamp=start_ts,
                end_timestamp=end_ts,
                page=page, rows=100,
            )
            if not batch:
                break
            all_orders.extend(batch)
            if len(batch) < 100:
                break
            page += 1

    completed = [o for o in all_orders if o.status in (OrderStatus.COMPLETED,)]
    completed.sort(key=lambda o: o.created_at)

    print(f"   Found {len(completed)} completed orders in 90 days\n")

    # Test chat access on each
    test_msg = (
        "\U0001f389 Transaction complete! Thank you for trading with us.\n"
        "Help other traders find us -- leave a quick review:\n"
        "https://trustpilot.com/review/axionexchange.io\n"
        "Your support means a lot! \U0001f499"
    )

    print(f"{'Order ID':<25} {'Date':<12} {'Side':<6} {'Fiat':<6} {'Amount':<12} {'Counterparty':<25} {'Chat OK?'}")
    print(f"{'─'*25} {'─'*12} {'─'*6} {'─'*6} {'─'*12} {'─'*25} {'─'*10}")

    success_count = 0
    fail_count = 0
    results = []

    for o in completed:
        order_id = o.external_id
        date_str = o.created_at.strftime("%Y-%m-%d")
        side = o.side.value
        fiat = o.fiat_currency.value
        amount = o.fiat_amount
        counterparty = o.counterparty.name if o.counterparty else "?"

        # Determine message language
        if fiat == "COP":
            msg = (
                "\U0001f389 Transaccion completada! Gracias por operar con nosotros.\n"
                "Ayuda a otros traders a encontrarnos -- dejanos una resena rapida:\n"
                "https://trustpilot.com/review/axionexchange.io\n"
                "Tu apoyo significa mucho! \U0001f499"
            )
        else:
            msg = test_msg

        try:
            result = await client.send_chat_message(order_id, msg)
            if result:
                status = "YES"
                success_count += 1
            else:
                status = "NO (null)"
                fail_count += 1
        except Exception as e:
            err = str(e)[:40]
            status = f"NO ({err})"
            fail_count += 1

        print(f"{order_id[-20:]:<25} {date_str:<12} {side:<6} {fiat:<6} {amount:<12} {counterparty:<25} {status}")
        results.append({"id": order_id, "date": date_str, "ok": "YES" in status})

        # Don't hammer API
        await asyncio.sleep(1.5)

    print(f"\n{'='*50}")
    print(f"  SUMMARY")
    print(f"  Chat accessible: {success_count}/{len(completed)}")
    print(f"  Chat blocked:    {fail_count}/{len(completed)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
