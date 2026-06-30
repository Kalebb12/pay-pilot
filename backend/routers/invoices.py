from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from services.nomba import nomba
import uuid
import schema
import models

router = APIRouter()


@router.post("/")
async def create_invoice(payload: schema.InvoiceCreate, db: Session = Depends(get_db)):
    # verify customer exists
    customer = db.query(models.Customer).filter(models.Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # save invoice
    invoice = models.Invoice(
        customer_id=payload.customer_id,
        amount_kobo=payload.amount_kobo,
        due_date=payload.due_date,
        description=payload.description,
        status="pending"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    account_ref = f"NMBINV-{invoice.id}-{uuid.uuid4().hex[:8]}"
    expiry_date = payload.due_date.strftime("%Y-%m-%d %H:%M:%S")

    # try creating VA — fall back to pool if sandbox limit hit
    try:
        va_data = await nomba.create_virtual_account(
            account_ref=account_ref,
            account_name=f"{customer.name} Invoice",
            expiry_date=expiry_date
        )
        va = models.VirtualAccount(
            invoice_id=invoice.id,
            account_ref=account_ref,
            account_number=va_data["bankAccountNumber"],
            bank_name=va_data["bankName"],
            bank_account_name=va_data["bankAccountName"],
            account_holder_id=va_data["accountHolderId"],
            expires_at=payload.due_date,
            active=True
        )
        db.add(va)
        db.commit()
        db.refresh(va)

    except Exception as e:
        if "2 sandbox virtual accounts" in str(e):
            # sandbox limit — grab from pool
            va = db.query(models.VirtualAccount)\
                .filter(models.VirtualAccount.invoice_id == None)\
                .filter(models.VirtualAccount.active == True)\
                .first()
            if not va:
                # clean up the saved invoice before raising
                db.delete(invoice)
                db.commit()
                raise HTTPException(
                    status_code=503,
                    detail="No virtual accounts available in pool. Sandbox limit reached."
                )
            va.invoice_id = invoice.id
            db.commit()
            db.refresh(va)
        else:
            db.delete(invoice)
            db.commit()
            raise HTTPException(status_code=500, detail=str(e))

    return {
        "invoice": invoice,
        "virtual_account": va,
        "customer_name": customer.name
    }


@router.get("/")
async def list_invoices(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    invoices = db.query(models.Invoice).filter(
        models.Invoice.customer_id == customer_id
    ).all()
    return {"customer": customer, "invoices": invoices}


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    customer = db.query(models.Customer)\
        .filter(models.Customer.id == invoice.customer_id)\
        .first()
    va = db.query(models.VirtualAccount)\
        .filter(models.VirtualAccount.invoice_id == invoice_id)\
        .first()
    return {
        "invoice": invoice,
        "virtual_account": va,
        "customer_name": customer.name if customer else None
    }


@router.get("/{invoice_id}/payment-page")
async def get_payment_page(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    customer = db.query(models.Customer)\
        .filter(models.Customer.id == invoice.customer_id)\
        .first()
    va = db.query(models.VirtualAccount)\
        .filter(models.VirtualAccount.invoice_id == invoice_id)\
        .first()
    if not va:
        raise HTTPException(status_code=404, detail="No virtual account assigned to this invoice")
    payments = db.query(models.Payment)\
        .filter(models.Payment.invoice_id == invoice_id)\
        .all()
    total_paid = sum(p.amount_kobo for p in payments)
    outstanding = invoice.amount_kobo - total_paid

    return {
        "invoice_id": invoice.id,
        "description": invoice.description,
        "amount_kobo": invoice.amount_kobo,
        "outstanding_kobo": outstanding,
        "status": invoice.status,
        "due_date": invoice.due_date,
        "customer_name": customer.name if customer else None,
        "virtual_account": {
            "account_number": va.account_number,
            "bank_name": va.bank_name,
            "bank_account_name": va.bank_account_name,
            "account_ref": va.account_ref
        }
    }


@router.patch("/{invoice_id}/status")
async def update_invoice_status(
    invoice_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    valid_statuses = ["pending", "partial", "paid", "overpaid", "overdue"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = status
    db.commit()
    return {"invoice_id": invoice_id, "status": status}


@router.delete("/va/{account_ref}")
async def release_account(account_ref: str, db: Session = Depends(get_db)):
    va = db.query(models.VirtualAccount)\
        .filter(models.VirtualAccount.account_ref == account_ref)\
        .first()
    # if not va:
    #     raise HTTPException(status_code=404, detail="Virtual account not found")
    # try:
    #     await nomba.expire_virtual_account(account_ref)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Nomba expire failed: {str(e)}")
    va.invoice_id = None
    va.active = True
    db.commit()
    return {"message": "Virtual account released back to pool"}