import asyncio
import sys
from pathlib import Path
from bson import ObjectId
from datetime import datetime, timezone

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.core.database import get_database
from app.core.security import create_access_token
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient


async def run_tests():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    print("=== STARTING SALES & PURCHASES COMPREHENSIVE TEST SUITE ===")

    # 1. Find verified demo user
    user = await db.users.find_one({"is_verified": True, "email": "demo@retailmind.ai"})
    if not user:
        user = await db.users.find_one({"is_verified": True})
    assert user is not None, "No verified test user found in DB"
    user_id = str(user["_id"])
    print(f"[OK] Using test user: {user.get('email')} (ID: {user_id})")

    token = create_access_token({"sub": user_id})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Find or create a test product
    product = await db.products.find_one({"user_id": user_id, "status": "active", "current_stock": {"$gt": 10}})
    if not product:
        product_doc = {
            "user_id": user_id,
            "name": "Test Product Automated",
            "sku": f"TST-{datetime.now().strftime('%M%S%f')}",
            "selling_price": 50.0,
            "cost_price": 30.0,
            "current_stock": 25,
            "minimum_stock": 5,
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await db.products.insert_one(product_doc)
        product = await db.products.find_one({"_id": res.inserted_id})
    product_id = str(product["_id"])
    initial_stock = product["current_stock"]
    print(f"[OK] Target product: '{product['name']}' (ID: {product_id}), Stock: {initial_stock}")

    # 3. Find or create a customer
    customer = await db.customers.find_one({"user_id": user_id})
    customer_id = str(customer["_id"]) if customer else None

    # 4. Find or create a supplier
    supplier = await db.suppliers.find_one({"user_id": user_id})
    supplier_id = str(supplier["_id"]) if supplier else None

    async with AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0) as ac:

        # ---------------------------------------------------------
        # TEST 1: Next Sale Number endpoint
        # ---------------------------------------------------------
        res = await ac.get("/api/sales/next-number", headers=headers)
        assert res.status_code == 200, f"GET /api/sales/next-number failed: {res.text}"
        next_sale_num = res.json().get("sale_number")
        assert next_sale_num and next_sale_num.startswith("SL-"), f"Invalid next sale number: {next_sale_num}"
        print(f"[OK] GET /api/sales/next-number -> {next_sale_num}")

        # ---------------------------------------------------------
        # TEST 2: Next Purchase Number endpoint
        # ---------------------------------------------------------
        res = await ac.get("/api/purchases/next-number", headers=headers)
        assert res.status_code == 200, f"GET /api/purchases/next-number failed: {res.text}"
        next_po_num = res.json().get("purchase_number")
        assert next_po_num and next_po_num.startswith("PO-"), f"Invalid next purchase number: {next_po_num}"
        print(f"[OK] GET /api/purchases/next-number -> {next_po_num}")

        # ---------------------------------------------------------
        # TEST 3: Create Partial Sale (with balance due, custom date)
        # ---------------------------------------------------------
        sale_payload = {
            "sale_number": next_sale_num,
            "sale_date": "2026-10-20",
            "customer_id": customer_id,
            "items": [{"product_id": product_id, "quantity": 2, "unit_price": 50.0}],
            "discount": 10.0,
            "discount_type": "amount",
            "payment_method": "upi",
            "payment_status": "partial",
            "amount_paid": 60.0,
            "balance_due": 30.0,
            "notes": "Automated partial sale test",
        }
        res = await ac.post("/api/sales/", json=sale_payload, headers=headers)
        assert res.status_code == 201, f"Create sale failed: {res.text}"
        sale_data = res.json()
        assert sale_data["subtotal"] == 100.0, f"Expected subtotal 100, got {sale_data['subtotal']}"
        assert sale_data["discount"] == 10.0, f"Expected discount 10, got {sale_data['discount']}"
        assert sale_data["total"] == 90.0, f"Expected total 90, got {sale_data['total']}"
        assert sale_data["payment_status"] == "partial", f"Expected partial, got {sale_data['payment_status']}"
        assert sale_data["amount_paid"] == 60.0, f"Expected amount_paid 60, got {sale_data['amount_paid']}"
        assert sale_data["balance_due"] == 30.0, f"Expected balance_due 30, got {sale_data['balance_due']}"
        assert sale_data["sale_number"] == next_sale_num, f"Sale number mismatch"
        print(f"[OK] Sale created: {sale_data['sale_number']} with total=90, paid=60, balance=30, status=partial")

        # Verify stock decreased exactly once
        updated_prod = await db.products.find_one({"_id": ObjectId(product_id)})
        assert updated_prod["current_stock"] == initial_stock - 2, (
            f"Expected stock {initial_stock - 2}, got {updated_prod['current_stock']}"
        )
        print(f"[OK] Product stock correctly decreased from {initial_stock} to {updated_prod['current_stock']}")

        # Verify inventory transaction
        txn = await db.inventory_transactions.find_one({"reference_id": sale_data["id"]})
        assert txn is not None, "Inventory transaction not found for sale"
        assert txn["quantity_change"] == -2, f"Expected -2 qty change, got {txn['quantity_change']}"
        print(f"[OK] Inventory transaction recorded: type={txn['transaction_type']}, change={txn['quantity_change']}")

        # ---------------------------------------------------------
        # TEST 4: Create Paid Sale
        # ---------------------------------------------------------
        paid_sale_payload = {
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 50.0}],
            "discount": 0.0,
            "payment_method": "cash",
            "payment_status": "paid",
            "notes": "Automated paid sale test",
        }
        res = await ac.post("/api/sales/", json=paid_sale_payload, headers=headers)
        assert res.status_code == 201, f"Create paid sale failed: {res.text}"
        paid_data = res.json()
        assert paid_data["total"] == 50.0
        assert paid_data["payment_status"] == "paid"
        assert paid_data["amount_paid"] == 50.0
        assert paid_data["balance_due"] == 0.0
        print(f"[OK] Paid sale created: {paid_data['sale_number']} total=50, paid=50, balance=0")

        # ---------------------------------------------------------
        # TEST 5: Create Unpaid Sale
        # ---------------------------------------------------------
        unpaid_sale_payload = {
            "items": [{"product_id": product_id, "quantity": 1, "unit_price": 50.0}],
            "discount": 0.0,
            "payment_method": "credit",
            "payment_status": "unpaid",
            "amount_paid": 0.0,
            "notes": "Automated unpaid sale test",
        }
        res = await ac.post("/api/sales/", json=unpaid_sale_payload, headers=headers)
        assert res.status_code == 201, f"Create unpaid sale failed: {res.text}"
        unpaid_data = res.json()
        assert unpaid_data["total"] == 50.0
        assert unpaid_data["payment_status"] == "unpaid"
        assert unpaid_data["amount_paid"] == 0.0
        assert unpaid_data["balance_due"] == 50.0
        print(f"[OK] Unpaid sale created: {unpaid_data['sale_number']} total=50, paid=0, balance=50")

        # ---------------------------------------------------------
        # TEST 6: Prevent Sales Exceeding Stock
        # ---------------------------------------------------------
        current_st = (await db.products.find_one({"_id": ObjectId(product_id)}))["current_stock"]
        excess_qty = current_st + 100
        excess_payload = {
            "items": [{"product_id": product_id, "quantity": excess_qty, "unit_price": 50.0}],
            "payment_status": "paid",
        }
        res = await ac.post("/api/sales/", json=excess_payload, headers=headers)
        assert res.status_code == 400, f"Expected 400 for excessive stock sale, got {res.status_code}: {res.text}"
        assert "Insufficient stock" in res.json().get("detail", ""), f"Unexpected error detail: {res.text}"
        # Ensure stock was NOT modified
        assert (await db.products.find_one({"_id": ObjectId(product_id)}))["current_stock"] == current_st
        print(f"[OK] Exceeding stock prevented with 400: '{res.json()['detail']}'")

        # ---------------------------------------------------------
        # TEST 7: Create Partial Purchase (with invoice # and date)
        # ---------------------------------------------------------
        stock_before_po = (await db.products.find_one({"_id": ObjectId(product_id)}))["current_stock"]
        po_payload = {
            "purchase_number": next_po_num,
            "purchase_date": "2026-10-18",
            "supplier_id": supplier_id,
            "supplier_invoice_number": "INV-TEST-2026-001",
            "items": [{"product_id": product_id, "quantity": 10, "unit_cost": 32.0}],
            "discount": 20.0,
            "payment_method": "bank_transfer",
            "payment_status": "partial",
            "amount_paid": 200.0,
            "balance_due": 100.0,
            "notes": "Automated purchase test",
        }
        res = await ac.post("/api/purchases/", json=po_payload, headers=headers)
        assert res.status_code == 201, f"Create purchase failed: {res.text}"
        po_data = res.json()
        assert po_data["subtotal"] == 320.0, f"Expected subtotal 320, got {po_data['subtotal']}"
        assert po_data["discount"] == 20.0, f"Expected discount 20, got {po_data['discount']}"
        assert po_data["total"] == 300.0, f"Expected total 300, got {po_data['total']}"
        assert po_data["supplier_invoice_number"] == "INV-TEST-2026-001", "Supplier invoice number mismatch"
        assert po_data["payment_status"] == "partial", f"Expected partial, got {po_data['payment_status']}"
        assert po_data["amount_paid"] == 200.0, f"Expected 200, got {po_data['amount_paid']}"
        assert po_data["balance_due"] == 100.0, f"Expected 100, got {po_data['balance_due']}"
        print(f"[OK] Purchase created: {po_data['purchase_number']} total=300, paid=200, balance=100, inv={po_data['supplier_invoice_number']}")

        # Verify stock increased exactly once
        stock_after_po = (await db.products.find_one({"_id": ObjectId(product_id)}))["current_stock"]
        assert stock_after_po == stock_before_po + 10, (
            f"Expected stock {stock_before_po + 10}, got {stock_after_po}"
        )
        print(f"[OK] Product stock correctly increased from {stock_before_po} to {stock_after_po}")

        # Verify product cost_price was updated to latest
        updated_cost = (await db.products.find_one({"_id": ObjectId(product_id)}))["cost_price"]
        assert updated_cost == 32.0, f"Expected cost_price 32.0, got {updated_cost}"
        print(f"[OK] Product cost price updated to latest: {updated_cost}")

        # Verify inventory transaction
        txn = await db.inventory_transactions.find_one({"reference_id": po_data["id"]})
        assert txn is not None, "Inventory transaction not found for purchase"
        assert txn["quantity_change"] == 10, f"Expected +10 qty change, got {txn['quantity_change']}"
        print(f"[OK] Inventory transaction recorded: type={txn['transaction_type']}, change={txn['quantity_change']}")

        # ---------------------------------------------------------
        # TEST 8: Create Unpaid Purchase
        # ---------------------------------------------------------
        unpaid_po_payload = {
            "items": [{"product_id": product_id, "quantity": 5, "unit_cost": 30.0}],
            "discount": 0.0,
            "payment_method": "credit",
            "payment_status": "unpaid",
            "notes": "Automated unpaid purchase test",
        }
        res = await ac.post("/api/purchases/", json=unpaid_po_payload, headers=headers)
        assert res.status_code == 201, f"Create unpaid purchase failed: {res.text}"
        unpaid_po_data = res.json()
        assert unpaid_po_data["total"] == 150.0
        assert unpaid_po_data["payment_status"] == "unpaid"
        assert unpaid_po_data["amount_paid"] == 0.0
        assert unpaid_po_data["balance_due"] == 150.0
        print(f"[OK] Unpaid purchase created: total=150, paid=0, balance=150")

        # ---------------------------------------------------------
        # TEST 9: Create Paid Purchase
        # ---------------------------------------------------------
        paid_po_payload = {
            "items": [{"product_id": product_id, "quantity": 5, "unit_cost": 30.0}],
            "discount": 0.0,
            "payment_method": "cash",
            "payment_status": "paid",
            "notes": "Automated paid purchase test",
        }
        res = await ac.post("/api/purchases/", json=paid_po_payload, headers=headers)
        assert res.status_code == 201, f"Create paid purchase failed: {res.text}"
        paid_po_data = res.json()
        assert paid_po_data["total"] == 150.0
        assert paid_po_data["payment_status"] == "paid"
        assert paid_po_data["amount_paid"] == 150.0
        assert paid_po_data["balance_due"] == 0.0
        print(f"[OK] Paid purchase created: total=150, paid=150, balance=0")

        # ---------------------------------------------------------
        # TEST 10: GET /api/sales/{id} and GET /api/purchases/{id}
        # ---------------------------------------------------------
        res = await ac.get(f"/api/sales/{sale_data['id']}", headers=headers)
        assert res.status_code == 200
        fetched_sale = res.json()
        assert fetched_sale["payment_status"] == "partial"
        assert fetched_sale["amount_paid"] == 60.0
        assert fetched_sale["balance_due"] == 30.0
        assert "sale_date" in fetched_sale and fetched_sale["sale_date"] is not None

        res = await ac.get(f"/api/purchases/{po_data['id']}", headers=headers)
        assert res.status_code == 200
        fetched_po = res.json()
        assert fetched_po["payment_status"] == "partial"
        assert fetched_po["amount_paid"] == 200.0
        assert fetched_po["balance_due"] == 100.0
        assert fetched_po["supplier_invoice_number"] == "INV-TEST-2026-001"
        assert "purchase_date" in fetched_po and fetched_po["purchase_date"] is not None
        print(f"[OK] Direct record retrieval verified with all enriched fields")

    client.close()
    print("\n=== ALL 10 TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    asyncio.run(run_tests())
