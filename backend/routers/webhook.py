from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from db import get_db
import models
import json

router = APIRouter()


@router.post("/")
async def webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    event_type = payload.get("event_type")
    request_id = payload.get("requestId")

    if event_type != "payment_success":
        return {"status": "ignored", "reason": f"unhandled event_type: {event_type}"}

    # idempotency check
    existing = db.query(models.LedgerLog)\
        .filter(models.LedgerLog.merchant_tx_ref == request_id)\
        .first()
    if existing:
        return {"status": "duplicate", "message": "already processed"}

    transaction = payload.get("data", {}).get("transaction", {})
    account_ref = transaction.get("aliasAccountReference")
    account_number = transaction.get("aliasAccountNumber")
    amount_naira = transaction.get("transactionAmount", 0)
    amount_kobo = int(amount_naira * 100)
    nomba_tx_ref = transaction.get("transactionId")
    customer_data = transaction.get("customer", {})
    sender_name = customer_data.get("senderName")
    sender_account = customer_data.get("accountNumber")
    sender_bank_code = customer_data.get("bankCode")

    # log raw event immediately — always, even if unmatched
    log = models.LedgerLog(
        invoice_id=None,
        merchant_tx_ref=request_id,
        event="payment.received",
        payload=json.dumps(payload)
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # find VA by account_ref
    va = db.query(models.VirtualAccount)\
        .filter(models.VirtualAccount.account_ref == account_ref)\
        .first()

    if not va or not va.invoice_id:
        log.event = "payment.unmatched"
        db.commit()
        return {"status": "unmatched", "message": "no invoice found for this virtual account"}

    invoice = db.query(models.Invoice)\
        .filter(models.Invoice.id == va.invoice_id)\
        .first()

    if not invoice:
        log.event = "payment.unmatched"
        db.commit()
        return {"status": "unmatched", "message": "invoice not found"}

    log.invoice_id = invoice.id
    db.commit()

    # invoice already closed — late/duplicate payment
    if invoice.status == "paid":
        log.event = "payment.on_closed_invoice"
        db.commit()
        # still record it for audit, but don't reconcile against this invoice
        payment = models.Payment(
            invoice_id=invoice.id,
            amount_kobo=amount_kobo,
            nomba_tx_ref=nomba_tx_ref,
            request_id=request_id,
            sender_name=sender_name,
            sender_account=sender_account,
            sender_bank_code=sender_bank_code,
            paid_at=datetime.now(timezone.utc)
        )
        db.add(payment)
        db.commit()
        return {"status": "payment_on_closed_invoice", "flagged": True}

    # record the payment
    payment = models.Payment(
        invoice_id=invoice.id,
        amount_kobo=amount_kobo,
        nomba_tx_ref=nomba_tx_ref,
        request_id=request_id,
        sender_name=sender_name,
        sender_account=sender_account,
        sender_bank_code=sender_bank_code,
        paid_at=datetime.now(timezone.utc)
    )
    db.add(payment)
    db.commit()

    # run reconciliation
    status = await reconcile_invoice(invoice, db)

    return {"status": status}


async def reconcile_invoice(invoice: models.Invoice, db: Session) -> str:
    expected = invoice.amount_kobo

    total_received = db.query(models.Payment)\
        .filter(models.Payment.invoice_id == invoice.id)\
        .with_entities(models.Payment.amount_kobo)\
        .all()
    total_received = sum(p[0] for p in total_received)

    difference = total_received - expected

    if difference == 0:
        new_status = "paid"
        flagged_reason = None
    elif difference < 0:
        new_status = "partial"
        flagged_reason = f"Underpaid by {abs(difference)} kobo. Outstanding: {abs(difference)} kobo."
    else:
        new_status = "overpaid"
        flagged_reason = f"Overpaid by {difference} kobo. Refund required."

    invoice.status = new_status
    db.commit()

    recon = models.Reconciliation(
        invoice_id=invoice.id,
        expected_kobo=expected,
        received_kobo=total_received,
        difference_kobo=difference,
        status="matched" if difference == 0 else ("underpaid" if difference < 0 else "overpaid"),
        flagged_reason=flagged_reason,
        flagged_at=datetime.now(timezone.utc) if flagged_reason else None
    )
    db.add(recon)
    db.commit()

    # release VA back to pool if invoice is closed
    if new_status == "paid":
        va = db.query(models.VirtualAccount)\
            .filter(models.VirtualAccount.invoice_id == invoice.id)\
            .first()
        if va:
            va.invoice_id = None
            db.commit()

    return new_status