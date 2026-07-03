from fastapi import FastAPI
from routers import invoices, virtual_accounts, webhook
from dotenv import load_dotenv
from db import engine, Base

Base.metadata.create_all(bind=engine)
load_dotenv()

app = FastAPI(title="NombaInvoice")

app.include_router(webhook.router, tags=["Webhook"])
app.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
app.include_router(virtual_accounts.router, prefix="/virtual-accounts", tags=["Virtual Accounts"])

@app.get("/health")
async def health():
  return {"status": "ok"}