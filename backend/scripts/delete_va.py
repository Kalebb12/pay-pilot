# scripts/cleanup_vas.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
load_dotenv()

from services.nomba import nomba

async def cleanup():
    vas = await nomba.filter_virtual_accounts(expired=False)
    print(f"Found {len(vas)} active VAs")
    for va in vas:
        account_ref = va["accountRef"]
        print(f"Expiring {account_ref}...")
        print(va)
        result = await nomba.expire_virtual_account(account_ref)
        print(f"Result: {result}")

asyncio.run(cleanup())