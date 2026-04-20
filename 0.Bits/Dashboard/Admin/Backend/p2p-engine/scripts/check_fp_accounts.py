"""Get full details of all COL/COP accounts."""
import asyncio
import httpx
import json

async def main():
    base = "https://api.facilitapay.com/api/v1"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{base}/sign_in",
            json={"user": {"username": "axion@axionexchange.io", "password": "Runningfrompoorsince2024!"}},
        )
        jwt = r.json()["jwt"]
        headers = {"Authorization": f"Bearer {jwt}"}

        r2 = await c.get(f"{base}/bank_accounts", headers=headers)
        accounts = r2.json()["data"]

        print(f"Total accounts: {len(accounts)}\n")

        # Print all accounts summary
        print("ALL ACCOUNTS SUMMARY:")
        print(f"{'Currency':8s} | {'Flow':10s} | {'Country':8s} | ID")
        print("-" * 80)
        for a in accounts:
            currency = str(a.get("currency", "?"))
            flow = str(a.get("flow_type") or a.get("type") or "N/A")
            country = str(a.get("branch_country") or "?")
            acct_id = a["id"]
            print(f"{currency:8s} | {flow:10s} | {country:8s} | {acct_id}")

        # Full details for COP and COL accounts
        print("\n\n=== COP ACCOUNT FULL DETAILS ===")
        cop_accounts = [a for a in accounts if a.get("currency") == "COP"]
        for a in cop_accounts:
            print(json.dumps(a, indent=2, default=str))

        print("\n=== COL-COUNTRY ACCOUNTS ===")
        col_accounts = [a for a in accounts if a.get("branch_country") == "COL"]
        for a in col_accounts:
            currency = str(a.get("currency", "?"))
            flow = str(a.get("flow_type") or "N/A")
            acct_id = a["id"]
            print(f"  {currency} | {flow} | {acct_id}")

        # Get balance on the COP account
        if cop_accounts:
            cop_id = cop_accounts[0]["id"]
            print(f"\n=== COP ACCOUNT BALANCE (id={cop_id}) ===")
            try:
                r3 = await c.get(f"{base}/bank_accounts/{cop_id}/balance", headers=headers)
                print(json.dumps(r3.json(), indent=2, default=str))
            except Exception as e:
                print(f"Error getting balance: {e}")

asyncio.run(main())
