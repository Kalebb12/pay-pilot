# scripts/expire_one.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
load_dotenv()

from services.nomba import nomba

async def expire():
    result = await nomba.expire_virtual_account("NMBINV-TEST-001-abcd1234")
    print(result)

asyncio.run(expire())

# {'createdAt': '2026-06-27T23:43:38.492Z', 'bankAccountNumber': '1523117332', 'bankAccountName': 'Nomba/Test Invoice Customer', 'bankName': 'Nombank MFB', 'accountRef': '', 'accountHolderId': '379f720c-e09d-49b9-bb30-59515fc26a97', 'accountName': 'Nomba Hackathon 2026/caleb John', 'currency': 'NGN', 'bvn': '1234567890', 'expiryDate': '2026-07-18T00:00:00', 'expired': False}