"""
Diagnostic: deep dive into the target user (adc123asdf@gmail.com) that matches
the reported scenario: 9 customers, 2 segmented, both "New Customers".
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml'))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from clustering.customer_segmentation import segment_customers, CustomerSegmentation


async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    target_uid = "6ac8a4b5526783a0c26e2259"
    print("=" * 80)
    print("TARGET USER: adc123asdf@gmail.com")
    print("=" * 80)

    # 1. All customers
    customers = await db.customers.find({"user_id": target_uid}).to_list(None)
    print(f"\n=== ALL {len(customers)} CUSTOMERS ===")
    for c in customers:
        print(f"  id={str(c['_id'])} name={c.get('name')} orders={c.get('total_orders')} "
              f"purchases={c.get('total_purchases')} last_purchase={c.get('last_purchase_date')}")

    # 2. All sales
    sales = await db.sales.find({"user_id": target_uid}).to_list(None)
    print(f"\n=== ALL {len(sales)} SALES ===")
    for s in sales:
        cid = s.get("customer_id")
        cname = s.get("customer_name")
        print(f"  sale={str(s['_id'])[:12]}.. customer_id={cid!r} customer_name={cname!r} "
              f"total={s.get('total')} created_at={s.get('created_at')}")

    # 3. Sales with vs without customer_id
    with_cid = [s for s in sales if s.get("customer_id")]
    without_cid = [s for s in sales if not s.get("customer_id")]
    print(f"\n=== SALES BREAKDOWN ===")
    print(f"Sales WITH customer_id: {len(with_cid)}")
    for s in with_cid:
        print(f"  cid={s['customer_id']} name={s.get('customer_name')} total={s.get('total')}")
    print(f"Sales WITHOUT customer_id: {len(without_cid)}")
    for s in without_cid:
        print(f"  customer_name={s.get('customer_name')!r} total={s.get('total')}")

    # 4. Check if walk-in sales have customer_name that matches a customer
    print(f"\n=== WALK-IN SALES CUSTOMER NAME MATCH ===")
    customer_names = {c["name"]: str(c["_id"]) for c in customers}
    for s in without_cid:
        cname = s.get("customer_name", "")
        match = customer_names.get(cname)
        print(f"  customer_name={cname!r} -> matches customer? {'YES id=' + match if match else 'NO'}")

    # 5. Now trace the EXACT segmentation
    print(f"\n=== SEGMENTATION TRACE ===")
    sales_data = [{"customer_id": s.get("customer_id"), "total": s.get("total", 0),
                   "created_at": s.get("created_at")} for s in sales]

    # Calculate RFM
    seg = CustomerSegmentation(n_clusters=4)
    rfm_matrix, customer_ids = seg.calculate_rfm(sales_data)
    print(f"RFM matrix shape: {rfm_matrix.shape}")
    print(f"Customer IDs: {customer_ids}")
    print(f"RFM values:")
    for cid, row in zip(customer_ids, rfm_matrix):
        print(f"  {cid}: recency={row[0]}, freq={row[1]}, monetary={row[2]}")

    # Run segmentation
    customer_segments, summary = segment_customers(sales_data, n_clusters=4)
    print(f"\ncustomer_segments mapping: {customer_segments}")
    print(f"\nsummary: {summary}")

    # 6. Check label assignment for each cluster
    print(f"\n=== CLUSTER LABEL ANALYSIS ===")
    seg2 = CustomerSegmentation(n_clusters=4)
    seg2.calculate_rfm(sales_data)
    seg2.fit(rfm_matrix)
    print(f"Actual n_clusters used: {seg2.n_clusters}")
    print(f"K-Means labels: {seg2.model.labels_}")
    for cid, profile in sorted(seg2.cluster_profiles.items()):
        print(f"  cluster {cid}: recency={profile['mean_recency']:.1f} freq={profile['mean_frequency']:.1f} "
              f"monetary={profile['mean_monetary']:.1f} count={profile['customer_count']} "
              f"label={profile['label']!r}")

    # 7. Trace the sample_customers bug
    print(f"\n=== SAMPLE_CUSTOMERS BUG TRACE ===")
    print(f"customer_segments (cid -> label): {customer_segments}")
    for seg_info in summary.get("segments", []):
        label = seg_info["label"]
        matched = [cid for cid, lab in customer_segments.items() if lab == label]
        print(f"\n  Segment label={label!r}")
        print(f"  Customers matched by LABEL: {matched}")
        print(f"  -> This is the bug: multiple clusters with same label match the SAME customers")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
