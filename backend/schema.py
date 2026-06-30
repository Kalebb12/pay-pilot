from __future__ import annotations

from datetime import datetime
from typing import Optional, Annotated, Any, Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic.types import StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: EmailStr
    phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=7, max_length=20)]

class CustomerCreate(CustomerBase):
    pass

class CustomerRead(CustomerBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Invoice Schemas ---
class InvoiceBase(BaseModel):
    customer_id: int
    amount_kobo: int
    description: str
    due_date: datetime

class InvoiceCreate(InvoiceBase):
    pass  # status set to "pending" by backend

class InvoiceRead(InvoiceBase):
    id: int
    status: Literal["pending", "partial", "paid", "overpaid", "overdue"]
    created_at: Optional[datetime] = None
    customer_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# --- Virtual Account Schemas ---
class VirtualAccountBase(BaseModel):
    invoice_id: Optional[int] = None
    account_number: NonEmptyStr
    bank_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    bank_account_name: NonEmptyStr
    account_holder_id: NonEmptyStr
    expires_at: Optional[datetime] = None
    active: bool = True

class VirtualAccountCreate(VirtualAccountBase):
    pass  # account_ref generated in backend, not accepted from client

class VirtualAccountRead(VirtualAccountBase):
    id: int
    account_ref: NonEmptyStr  # returned in response
    model_config = ConfigDict(from_attributes=True)


# --- Payment Schemas ---
class PaymentBase(BaseModel):
    invoice_id: int
    amount_kobo: int
    nomba_tx_ref: NonEmptyStr
    request_id: NonEmptyStr

class PaymentCreate(PaymentBase):
    pass

class PaymentRead(PaymentBase):
    id: int
    paid_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Reconciliation Schemas ---
class ReconciliationBase(BaseModel):
    invoice_id: int
    expected_kobo: int
    received_kobo: int
    difference_kobo: int
    flagged_reason: Optional[str] = None
    status: Literal["matched", "underpaid", "overpaid", "overdue", "late"] = "matched"

class ReconciliationCreate(ReconciliationBase):
    pass

class ReconciliationRead(ReconciliationBase):
    id: int
    flagged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- LedgerLog Schemas ---
class LedgerLogBase(BaseModel):
    invoice_id: Optional[int] = None 
    merchant_tx_ref: NonEmptyStr
    event: NonEmptyStr
    payload: dict[str, Any]

class LedgerLogCreate(LedgerLogBase):
    pass

class LedgerLogRead(LedgerLogBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Refund Schemas ---
class RefundBase(BaseModel):
    payment_id: int
    amount_kobo: int
    status: Literal["pending", "completed", "failed"] = "pending"
    nomba_tx_ref: NonEmptyStr
    completed_at: Optional[datetime] = None

class RefundCreate(RefundBase):
    pass

class RefundRead(RefundBase):
    id: int
    initiated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)