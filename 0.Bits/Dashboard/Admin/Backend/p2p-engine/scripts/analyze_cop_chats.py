"""
Analyze COP order chats from today to find common drop-off patterns.
Reads Binance chats for all awaiting_info, cancelled, and link_sent orders.
"""
import asyncio
import sqlite3
import os
import sys
import json
from collections import Counter
from datetime import datetime

sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from src.fiat.cop.binance_chat import BinanceChatClient


async def main():
    client = BinanceChatClient(
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET"),
    )

    conn = sqlite3.connect("data/cop_orders.db")
    conn.row_factory = sqlite3.Row

    # Get all today's non-completed orders
    cur = conn.cursor()
    cur.execute("""
        SELECT binance_order_id, state, amount_cop, amount_usdt, created_at
        FROM cop_orders
        WHERE created_at >= '2026-02-15'
        ORDER BY created_at
    """)
    rows = cur.fetchall()

    target_states = {"awaiting_info", "cancelled", "link_sent", "manual_review", "info_received"}
    orders = [r for r in rows if r["state"] in target_states]

    print(f"=== Analyzing {len(orders)} non-completed COP orders from today ===\n")

    # Track patterns
    patterns = Counter()
    no_customer_msg = 0
    customer_replied = 0
    chat_details = []

    for i, order in enumerate(orders):
        oid = order["binance_order_id"]
        state = order["state"]
        cop = float(order["amount_cop"] or 0)

        try:
            messages = await client.get_chat_messages(oid)
        except Exception as e:
            print(f"  [{i+1}/{len(orders)}] {oid[-10:]} — chat error: {e}")
            patterns["chat_error"] += 1
            continue

        # Separate self vs customer messages
        self_msgs = []
        customer_msgs = []
        for msg in messages:
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            # Skip system/JSON messages
            if content.startswith("{") and "type" in content.lower():
                continue
            if msg.get("self", False):
                self_msgs.append(content)
            else:
                customer_msgs.append(content)

        # Classify
        has_customer_reply = len(customer_msgs) > 0
        if has_customer_reply:
            customer_replied += 1
        else:
            no_customer_msg += 1

        # Analyze customer messages for common patterns
        all_customer_text = " ".join(customer_msgs).lower()

        order_info = {
            "order_id": oid[-14:],
            "state": state,
            "cop": cop,
            "customer_msgs": len(customer_msgs),
            "self_msgs": len(self_msgs),
            "customer_text": customer_msgs[:3],  # First 3 messages
            "pattern": [],
        }

        if not has_customer_reply:
            order_info["pattern"].append("NO_REPLY")
            patterns["no_customer_reply"] += 1
        else:
            # Check for common patterns in customer text
            if any(w in all_customer_text for w in ["nequi", "daviplata", "efecty"]):
                order_info["pattern"].append("WANTS_NON_PSE")
                patterns["wants_non_pse_method"] += 1
            if any(w in all_customer_text for w in ["bancolombia", "banco", "davivienda", "bbva", "scotiabank"]):
                order_info["pattern"].append("MENTIONS_BANK")
                patterns["mentions_bank"] += 1
            if any(w in all_customer_text for w in ["como", "cómo", "how", "que hago", "qué hago", "no entiendo", "no se", "no sé"]):
                order_info["pattern"].append("CONFUSED")
                patterns["confused_how_to_pay"] += 1
            if any(w in all_customer_text for w in ["link", "enlace", "pse"]):
                order_info["pattern"].append("MENTIONS_LINK_PSE")
                patterns["mentions_link_pse"] += 1
            if any(w in all_customer_text for w in ["cuenta", "ahorros", "corriente", "account"]):
                order_info["pattern"].append("GIVES_ACCOUNT_INFO")
                patterns["gives_account_info"] += 1
            if any(w in all_customer_text for w in ["pagu", "pagué", "pague", "transferi", "transferí", "ya pag", "hice el pago", "listo"]):
                order_info["pattern"].append("CLAIMS_PAID")
                patterns["claims_paid"] += 1
            if any(w in all_customer_text for w in ["cancel", "cancela"]):
                order_info["pattern"].append("WANTS_CANCEL")
                patterns["wants_cancel"] += 1
            if any(w in all_customer_text for w in ["hola", "hello", "buenas", "buenos"]):
                order_info["pattern"].append("GREETING_ONLY")
            if any(w in all_customer_text for w in ["comprobante", "recibo", "receipt", "proof"]):
                order_info["pattern"].append("SENDS_PROOF")
                patterns["sends_proof"] += 1
            if not order_info["pattern"]:
                order_info["pattern"].append("OTHER")
                patterns["other_reply"] += 1

        chat_details.append(order_info)

        # Print progress every 10
        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(orders)} orders...")

        # Small delay to avoid rate-limiting
        await asyncio.sleep(0.15)

    print(f"\n{'='*80}")
    print(f"=== ANALYSIS RESULTS ===")
    print(f"{'='*80}\n")

    print(f"Total orders analyzed: {len(orders)}")
    print(f"  Customer replied:    {customer_replied}")
    print(f"  No customer reply:   {no_customer_msg}")
    print()

    print("=== PATTERN BREAKDOWN ===")
    for pattern, count in patterns.most_common():
        pct = count / len(orders) * 100
        print(f"  {pattern:30s}: {count:3d} ({pct:.1f}%)")

    print(f"\n{'='*80}")
    print(f"=== BY STATE ===")
    print(f"{'='*80}")
    state_patterns = {}
    for d in chat_details:
        s = d["state"]
        if s not in state_patterns:
            state_patterns[s] = Counter()
        for p in d["pattern"]:
            state_patterns[s][p] += 1
    for state, pcounts in sorted(state_patterns.items()):
        total_in_state = sum(1 for d in chat_details if d["state"] == state)
        print(f"\n  {state} ({total_in_state} orders):")
        for p, c in pcounts.most_common():
            print(f"    {p:30s}: {c}")

    print(f"\n{'='*80}")
    print(f"=== SAMPLE CHATS (orders where customer replied) ===")
    print(f"{'='*80}")
    replied = [d for d in chat_details if d["customer_msgs"] > 0]
    for d in replied[:30]:
        print(f"\n  Order {d['order_id']} | {d['state']} | COP {d['cop']:,.0f} | patterns={d['pattern']}")
        for msg in d["customer_text"]:
            # Truncate long messages
            display = msg[:120] + "..." if len(msg) > 120 else msg
            print(f"    💬 {display}")

    await client.close()
    conn.close()


asyncio.run(main())
