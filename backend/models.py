from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    invoices = relationship("Invoice", back_populates="customer")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount_kobo = Column(BigInteger, nullable=False)  # always integer kobo
    status = Column(String(20), nullable=False, default="pending")
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    customer = relationship("Customer", back_populates="invoices")
    virtual_account = relationship("VirtualAccount", back_populates="invoice", uselist=False)
    payments = relationship("Payment", back_populates="invoice")
    reconciliations = relationship("Reconciliation", back_populates="invoice")
    ledger_logs = relationship("LedgerLog", back_populates="invoice")


class VirtualAccount(Base):
    __tablename__ = "virtual_accounts"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    account_number = Column(String(20), unique=True, nullable=False, index=True)
    bank_name = Column(String(50), nullable=False)
    bank_account_name = Column(String(100), nullable=False)
    account_holder_id = Column(String(100), nullable=False)
    account_ref = Column(String(100), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, default=True)

    invoice = relationship("Invoice", back_populates="virtual_account")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount_kobo = Column(BigInteger, nullable=False)
    paid_at = Column(DateTime(timezone=True), default=utcnow)
    nomba_tx_ref = Column(String(100), unique=True, nullable=False, index=True)
    request_id = Column(String(100), unique=True, nullable=False, index=True)
    sender_name = Column(String(100), nullable=True)
    sender_account = Column(String(20), nullable=True)
    sender_bank_code = Column(String(20), nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
    refund = relationship("Refund", back_populates="payment", uselist=False)


class Reconciliation(Base):
    __tablename__ = "reconciliation"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    expected_kobo = Column(BigInteger, nullable=False)
    received_kobo = Column(BigInteger, nullable=False)
    difference_kobo = Column(BigInteger, nullable=False)
    flagged_reason = Column(Text, nullable=True)  # nullable — not every recon is flagged
    status = Column(String(20), nullable=False, default="matched")
    flagged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    invoice = relationship("Invoice", back_populates="reconciliations")


class LedgerLog(Base):
    __tablename__ = "ledger_log"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)  # nullable for unmatched
    merchant_tx_ref = Column(String(100), nullable=False, index=True)
    event = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)  # store as JSON string
    response_status = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    invoice = relationship("Invoice", back_populates="ledger_logs")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    amount_kobo = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    nomba_tx_ref = Column(String(100), unique=True, nullable=False, index=True)
    initiated_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    payment = relationship("Payment", back_populates="refund")

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True)

    business_name = Column(String(150))
    owner_name = Column(String(100))

    phone = Column(String(20), unique=True)
    email = Column(String(100), unique=True)

    nomba_client_id = Column(Text)
    nomba_private_key = Column(Text)
    nomba_account_id = Column(String(100))

    onboarding_completed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    customers = relationship("Customer")
    invoices = relationship("Invoice")