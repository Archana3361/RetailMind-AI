#!/usr/bin/env python3
"""Detailed database analysis - view data per user and verify schemas"""

import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings


async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        await db.command("ping")
        print("✓ MongoDB connected\n")
        
        # Get all users
        users = await db.users.find({}, {"email": 1, "_id": 1, "is_verified": 1}).to_list(None)
        print(f"="*70)
        print("DETAILED DATA ANALYSIS BY USER")
        print("="*70)
        
        for user in users:
            user_id = str(user["_id"])
            email = user.get("email")
            verified = user.get("is_verified")
            
            if not verified:
                print(f"\n⊘ {email} (NOT VERIFIED - skipping)")
                continue
            
            print(f"\n{'─'*70}")
            print(f"User: {email}")
            print(f"ID: {user_id}")
            print(f"{'─'*70}")
            
            # Count records for this user
            products = await db.products.count_documents({"user_id": user_id})
            customers = await db.customers.count_documents({"user_id": user_id})
            suppliers = await db.suppliers.count_documents({"user_id": user_id})
            sales = await db.sales.count_documents({"user_id": user_id})
            purchases = await db.purchases.count_documents({"user_id": user_id})
            user_categories = await db.categories.count_documents({"user_id": user_id})
            
            print(f"\nRecords owned by this user:")
            print(f"  Products:   {products}")
            print(f"  Customers:  {customers}")
            print(f"  Suppliers:  {suppliers}")
            print(f"  Sales:      {sales}")
            print(f"  Purchases:  {purchases}")
            print(f"  Categories: {user_categories} (user-scoped)")
            
            # Show sample records
            if products > 0:
                p = await db.products.find_one({"user_id": user_id})
                print(f"\n  Sample Product:")
                print(f"    Name: {p.get('name')}")
                print(f"    SKU: {p.get('sku')}")
                print(f"    Stock: {p.get('current_stock')}")
                print(f"    Price: ${p.get('selling_price')}")
                print(f"    Supplier: {p.get('supplier_name')}")
            
            if suppliers > 0:
                s = await db.suppliers.find_one({"user_id": user_id})
                print(f"\n  Sample Supplier:")
                print(f"    Name: {s.get('name')}")
                print(f"    Email: {s.get('email')}")
                print(f"    Phone: {s.get('phone')}")
            
            if customers > 0:
                c = await db.customers.find_one({"user_id": user_id})
                print(f"\n  Sample Customer:")
                print(f"    Name: {c.get('name')}")
                print(f"    Email: {c.get('email')}")
                print(f"    Phone: {c.get('phone')}")
        
        # Global categories
        print(f"\n{'─'*70}")
        print("GLOBAL CATEGORIES (Shared)")
        print(f"{'─'*70}")
        categories = await db.categories.find({}, {"name": 1, "_id": 1}).to_list(None)
        print(f"Total: {len(categories)}")
        for i, cat in enumerate(categories[:10], 1):
            print(f"  {i}. {cat.get('name')}")
        
        # Schema verification
        print(f"\n{'='*70}")
        print("SCHEMA VERIFICATION")
        print(f"{'='*70}")
        
        # Check product schema
        prod = await db.products.find_one({})
        if prod:
            print(f"\nProduct fields: {sorted(prod.keys())}")
        
        # Check supplier schema
        supp = await db.suppliers.find_one({})
        if supp:
            print(f"\nSupplier fields: {sorted(supp.keys())}")
        
        # Check category schema
        cat = await db.categories.find_one({})
        if cat:
            print(f"\nCategory fields: {sorted(cat.keys())}")
            print(f"  Has user_id: {'user_id' in cat}")
        
        print(f"\n{'='*70}")
        
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
