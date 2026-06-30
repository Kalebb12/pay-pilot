import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
load_dotenv()

from services.nomba import nomba

async def test():
    result = await nomba.create_virtual_account(
        account_ref="NMBINV-TEST-010-abcd1234",
        account_name="Test Invoice Customer",
        expiry_date="2026-07-18 00:00:00",
    )
    print(result)

asyncio.run(test())