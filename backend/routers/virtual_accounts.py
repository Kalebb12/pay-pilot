from fastapi import APIRouter, HTTPException
from services.nomba import nomba

router = APIRouter()

@router.get("/{account_ref}")
async def get_virtual_account(account_ref: str):
    try:
        data = await nomba.fetch_virtual_account(account_ref)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{account_ref}")
async def expire_virtual_account(account_ref: str):
    try:
        data = await nomba.expire_virtual_account(account_ref)
        return {"msg": "expired", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_virtual_accounts(expired: bool = False):
    try:
        results = await nomba.filter_virtual_accounts(expired=expired)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
