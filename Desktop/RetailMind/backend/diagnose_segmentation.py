"""
Diagnostic: trace the complete data flow for customer segmentation.
Inspects actual MongoDB records and RFM calculation.
"""
import asyncio
import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    # Find the demo user with sales
    pipeline = [
        {"$group": {"_id": "$user_id", "sales_count": {"$sum": 1}}},
        {"$sort": {"sales_count": -1}},
        {"$limit": 1}
    ]
    top = await db.sales.aggregate(pipeline).to_list(1)
    if not top:
        print("[FAIL] No sales found at all")
        return
    user_id = top[0]["_id"]
    print(f"User ID: {user_id}")
    print(f"Total sales: {top[0]['sales_count']}")

    # 1. Count total customers
    total_customers = await db.customers.count_documents({"user_id": user_id})
    print(f"\n=== CUSTOMERS ===")
    print(f"Total customers in DB: {total_customers}")

    # 2. Inspect all customers
    customers = await db.customers.find({"user_id": user_id}).to_list(None)
    print(f"\nCustomer list (id, name, total_orders, total_purchases, last_purchase_date):")
    for c in customers:
        print(f"  id={str(c['_id'])} name={c.get('name')} orders={c.get('total_orders')} "
              f"purchases={c.get('total_purchases')} last_purchase={c.get('last_purchase_date')}")

    # 3. Inspect all sales
    sales = await db.sales.find({"user_id": user_id}).to_list(None)
    print(f"\n=== SALES ({len(sales)} records) ===")
    print(f"\nSales detail (id, customer_id type, customer_id value, customer_name, total, created_at):")
    for s in sales:
        cid = s.get("customer_id")
        cid_type = type(cid).__name__
        print(f"  sale={str(s['_id'])[:12]}.. customer_id={cid!r} (type={cid_type}) "
              f"customer_name={s.get('customer_name','N/A')!r} total={s.get('total')} "
              f"created_at={s.get('created_at')}")

    # 4. Check how many sales have a valid customer_id
    sales_with_cid = [s for s in sales if s.get("customer_id")]
    sales_without_cid = [s for s in sales if not s.get("customer_id")]
    print(f"\n=== CUSTOMER ID ANALYSIS ===")
    print(f"Sales WITH customer_id: {len(sales_with_cid)}")
    print(f"Sales WITHOUT customer_id (walk-in): {len(sales_without_cid)}")

    # 5. Check distinct customer_ids in sales vs customer collection
    distinct_cids_in_sales = set()
    for s in sales_with_cid:
        distinct_cids_in_sales.add(str(s["customer_id"]))
    customer_ids_set = set(str(c["_id"]) for c in customers)
    print(f"\nDistinct customer_ids referenced in sales: {len(distinct_cids_in_sales)}")
    print(f"  IDs: {distinct_cids_in_sales}")
    print(f"\nCustomer IDs in customers collection: {len(customer_ids_set)}")
    print(f"  IDs: {customer_ids_set}")
    print(f"\nCustomer IDs in sales but NOT in customers collection: {distinct_cids_in_sales - customer_ids_set}")
    print(f"Customer IDs in collection but NOT referenced in sales: {customer_ids_set - distinct_cids_in_sales}")

    # 6. Now trace the RFM calculation exactly as the service does
    print(f"\n=== RFM CALCULATION TRACE ===")
    # Replicate get_customer_segmentation logic
    sales_data = []
    for sale in sales:
        sales_data.append({
            "customer_id": sale.get("customer_id"),
            "total": sale.get("total", 0),
            "created_at": sale.get("created_at")
        })

    # Replicate calculate_rfm
    customer_data = {}
    for sale in sales_data:
        customer_id = sale.get("customer_id")
        if not customer_id:
            continue
        customer_id = str(customer_id)
        total = float(sale.get("total", 0))
        created_at = sale.get("created_at")
        if customer_id not in customer_data:
            customer_data[customer_id] = {
                "last_purchase": created_at,
                "purchase_count": 0,
                "total_spent": 0.0
            }
        customer_data[customer_id]["purchase_count"] += 1
        customer_data[customer_id]["total_spent"] += total
        if created_at:
            if customer_data[customer_id]["last_purchase"] is None or created_at > customer_data[customer_id]["last_purchase"]:
                customer_data[customer_id]["last_purchase"] = created_at

    print(f"Customers with sales (after grouping): {len(customer_data)}")
    print(f"\nRFM per customer:")
    ref_date = datetime.now(timezone.utc)
    for cid, data in customer_data.items():
        lp = data["last_purchase"]
        if lp:
            if isinstance(lp, str):
                lp_dt = datetime.fromisoformat(lp.replace("Z", "+00:00"))
            else:
                lp_dt = lp
            if lp_dt.tzinfo is None:
                lp_dt = lp_dt.replace(tzinfo=timezone.utc)
            recency = (ref_date - lp_dt).days
        else:
            recency = 999
        print(f"  cid={cid} recency={recency} freq={data['purchase_count']} "
              f"monetary={data['total_spent']:.2f} last_purchase={lp}")

    # 7. Check created_at types
    print(f"\n=== CREATED_AT TYPE CHECK ===")
    for s in sales[:3]:
        ca = s.get("created_at")
        print(f"  sale {str(s['_id'])[:12]}.. created_at={ca!r} type={type(ca).__name__}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
