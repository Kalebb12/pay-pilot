# scripts/seed.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from db import SessionLocal
import models

def seed():
    db = SessionLocal()
    try:
        # skip if already seeded
        if db.query(models.Customer).count() > 0:
            print("DB already seeded. Skipping.")
            return

        # --- Customers ---
        customer_a = models.Customer(
            name="Adaeze Okonkwo",
            email="adaeze@example.com",
            phone="08012345678"
        )
        customer_b = models.Customer(
            name="Emeka Nwosu",
            email="emeka@example.com",
            phone="08087654321"
        )
        db.add_all([customer_a, customer_b])
        db.commit()
        db.refresh(customer_a)
        db.refresh(customer_b)
        print(f"Created customers: {customer_a.id}, {customer_b.id}")

        # --- Persistent Virtual Accounts (your 4 sandbox VAs) ---
        # These are pre-seeded — not created via Nomba API
        # invoice_id=None means available in pool
        va1 = models.VirtualAccount(
            invoice_id=None,
            account_ref="parent-va-001",
            account_number="3049420327",
            bank_name="Nombank MFB",
            bank_account_name="Nomba/Test Customer VA",
            account_holder_id="f666ef9b-888e-4799-85ce-acb505b28023",
            expires_at=None,
            active=True
        )
        va2 = models.VirtualAccount(
            invoice_id=None,
            account_ref="parent-va-002",
            account_number="9882319033",
            bank_name="Nombank MFB",
            bank_account_name="Nomba/HoldEgo Gate2",
            account_holder_id="f666ef9b-888e-4799-85ce-acb505b28023",
            expires_at=None,
            active=True
        )
        va3 = models.VirtualAccount(
            invoice_id=None,
            account_ref="sub-va-001",
            account_number="1523117332",
            bank_name="Nombank MFB",
            bank_account_name="Nomba/Test Invoice Customer",
            account_holder_id="379f720c-e09d-49b9-bb30-59515fc26a97",
            expires_at=None,
            active=True
        )
        db.add_all([va1, va2, va3])
        db.commit()
        print(f"Seeded 3 virtual accounts into pool")

        print("Seed complete.")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()