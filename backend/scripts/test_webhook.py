import httpx, asyncio, uuid

WEBHOOK_URL= "http://127.0.0.1:8000/"

async def simulate_payment(account_ref: str, amount_naira: float, sender_name: str = "CALEB CHUKWUEMEKA JOHNOKORIE"):
    payload = {
        "event_type": "payment_success",
        "requestId": str(uuid.uuid4()),
        "walletBalance": 180.0,
        "data": {
            "merchant": {
                "walletId": "6a3beef8ff2cf788e4bd0bb8",
                "userId": "379f720c-e09d-49b9-bb30-59515fc26a97"
            },
            "terminal": {},
            "transaction": {
                "fee": 10.0,
                "sessionId": str(uuid.uuid4()),
                "transactionId": f"API-VACT_TRA-TEST-{uuid.uuid4().hex[:8]}",
                "type": "vact_transfer",
                "aliasAccountName": "Nomba Hackathon 2026/caleb John",
                "narration": f"Transfer from {sender_name}",
                "transactionAmount": amount_naira,
                "originatingFrom": "api",
                "time": "2026-06-30T11:36:34Z",
                "responseCode": "",
                "aliasAccountType": "VIRTUAL_SANDBOX",
                "aliasAccountReference": account_ref,
                "aliasAccountNumber": "9968187521",
                "customer": {
                    "bankCode": "305",
                    "bankName": "Paycom (Opay)",
                    "senderName": sender_name,
                    "accountNumber": "8115089660"
                }
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(WEBHOOK_URL, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

# test scenarios
async def main():
    account_ref = "NMBINV-3-7d22ae46"  # replace with your actual account_ref

    print("--- Exact payment ---")
    await simulate_payment(account_ref, 100.0)

    print("--- Underpayment ---")
    # await simulate_payment(account_ref, 50.0)

    print("--- Overpayment ---")
    # await simulate_payment(account_ref, 150.0)

asyncio.run(main())