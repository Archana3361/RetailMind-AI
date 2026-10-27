"""
Diagnostic: check ALL users, their customer counts, sales, and segmentation results.
Find the user that matches the reported scenario (9 customers, 2 segmented).
"""
import asyncio
import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add ml to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml'))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.analytics_service import get_customer_segmentation


async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    # Get ALL users
    users = await db.users.find({}, {"email": 1}).to_list(None)
    print(f"Total users in DB: {len(users)}")
    print("=" * 80)

    for user in users:
        user_id = str(user["_id"])
        email = user.get("email", "?")

        cust_count = await db.customers.count_documents({"user_id": user_id})
        sales_count = await db.sales.count_documents({"user_id": user_id})
        sales_with_cid = await db.sales.count_documents({"user_id": user_id, "customer_id": {"$ne": None, "$exists": True}})

        print(f"\nUser: {email} (id: {user_id})")
        print(f"  customers: {cust_count}, sales: {sales_count}, sales_with_customer_id: {sales_with_cid}")

        if sales_count == 0:
            print("  -> No sales, skipping segmentation")
            continue

        # Run the actual segmentation service
        try:
            result = await get_customer_segmentation(db, user_id)
            if "error" in result:
                print(f"  -> ERROR: {result['error']}")
                if "message" in result:
                    print(f"     {result['message']}")
            else:
                print(f"  -> total_customers segmented: {result.get('total_customers')}")
                print(f"  -> total_clusters: {result.get('total_clusters')}")
                print(f"  -> segments: {len(result.get('segments', []))}")
                for seg in result.get("segments", []):
                    print(f"     - {seg['label']}: {seg['customer_count']} customers, "
                          f"recency={seg.get('avg_recency_days')}, freq={seg.get('avg_purchases')}, "
                          f"spent={seg.get('avg_total_spent')}, sample={seg.get('sample_customers', [])[:3]}")
        except Exception as e:
            print(f"  -> EXCEPTION: {e}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
