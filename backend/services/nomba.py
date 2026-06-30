import httpx
import os
import time

class NombaClient:
  BASE_URL = os.getenv("NOMBA_BASE_URL")

  def __init__(self):
    self.client_id = os.getenv("NOMBA_CLIENT_ID")
    self.private_key = os.getenv("NOMBA_PRIVATE_KEY")
    self.account_id = os.getenv("NOMBA_ACCOUNT_ID")
    self.sub_account_id = os.getenv("NOMBA_SUB_ACCOUNT_ID")
    self._access_token = None
    self._refresh_token = None
    self._expires_at = 0
  
  async def get_token(self) -> str:
    now = time.time()
    if self._access_token and now < self._expires_at - 300:
      return self._access_token
    if self._refresh_token:
      return await self._refresh()
    return await self._issue()
  
  async def _issue(self) -> str:
    async with httpx.AsyncClient() as client:
      response = await client.post(
        f"{self.BASE_URL}/auth/token/issue",
        json={
          "grant_type": "client_credentials",
          "client_id": self.client_id,
          "client_secret": self.private_key
        },
        headers={
          "Content-Type": "application/json",
          "accountId": self.account_id
        }
      )

      data = response.json()
      if data["code"] != "00":
        raise Exception(f"Token issue failed: {data}")

      return self._store(data["data"])

  async def _refresh(self) -> str:
    async with httpx.AsyncClient() as client:
      response = await client.post(
        f"{self.BASE_URL}/auth/token/refresh",
        json={
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token
        },   
      )
      data = response.json()
      if data["code"] != "00":
        self._refresh_token = None
        return await self._issue()
      return self._store(data["data"])
    
  def _store(self, data: dict) -> str:
    self._access_token = data["access_token"]
    if data.get("refresh_token"):
      self._refresh_token = data["refresh_token"]
    self._expires_at = time.time() + data.get("expires_in", 3600)
    return self._access_token
  
  async def _headers(self) -> dict:
    token = await self.get_token()
    return {
        "Authorization": f"Bearer {token}",
        "accountId": self.account_id,
        "Content-Type": "application/json"
    }
  
  async def create_virtual_account(
    self,
    account_ref: str,
    account_name: str,
    expiry_date: str = None
    ) -> dict:
    payload = {
        "accountRef": account_ref,
        "accountName": account_name,
        "currency": "NGN"
    }
    if expiry_date:
        payload["expiryDate"] = expiry_date

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.BASE_URL}/accounts/virtual/{self.sub_account_id}",
            json=payload,
            headers=await self._headers()
        )
        data = response.json()
        if data["code"] != "00":
            raise Exception(f"Virtual account creation failed: {data}")
        return data["data"]
            
  async def filter_virtual_accounts(self, expired: bool = False) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.BASE_URL}/accounts/virtual/list",
            json={"expired": expired},
            headers={
                "Authorization": f"Bearer {await self.get_token()}",
                "accountId": self.account_id,
                "Content-Type": "application/json"
            }
        )
        data = response.json()
        if data["code"] != "00":
            raise Exception(f"Filter failed: {data}")
        return data["data"]["results"]
    
  async def expire_virtual_account(self, account_ref: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{self.BASE_URL}/accounts/virtual/{account_ref}",
            headers=await self._headers()
        )
        data = response.json()
        if data["code"] != "00":
            raise Exception(f"Expire failed: {data}")
        
        return data["data"]
    
  async def fetch_virtual_account(self, account_ref: str) -> dict:
    async with httpx.AsyncClient() as client:
      response = await client.get(
        f"{self.BASE_URL}/accounts/virtual/{account_ref}",
        headers=await self._headers()
      )
      data = response.json()
      if data["code"] != "00":
        raise Exception(f"Fetch failed: {data}")
      return data["data"]
        

nomba = NombaClient()