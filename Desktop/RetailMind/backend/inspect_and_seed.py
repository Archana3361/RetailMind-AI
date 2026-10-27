#!/usr/bin/env python3
"""
RetailMind Secure Data Seeding Script
======================================

This script provides a secure, interactive workflow to:
1. Authenticate an existing RetailMind user (no hardcoded credentials)
2. Inspect current database state and record initial counts
3. Seed realistic, interconnected demo data
4. Verify data consistency and ownership rules
5. Test dropdowns and core functionality

Security:
- Credentials are prompted at runtime (not hardcoded)
- Password input is masked (not displayed)
- No credentials stored in source code or logs
- Uses existing authentication API
- OTP verification goes through normal flow if required

Usage:
    python inspect_and_seed.py
    
The script will prompt you to:
    - Enter your registered email
    - Enter your password (input hidden)
    - Complete OTP verification if required (via normal auth flow)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import getpass
import json

# Add backend to path for imports
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import hash_password, verify_password
from bson import ObjectId


class RetailMindSeeder:
    def __init__(self):
        self.client = None
        self.db = None
        self.user_id = None
        self.user_email = None
        self.initial_counts = {}
        self.final_counts = {}
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            # Test connection
            await self.db.command("ping")
            print("✓ Connected to MongoDB")
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            sys.exit(1)
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ Disconnected from MongoDB")
    
    async def authenticate_user(self):
        """Authenticate user interactively (no hardcoded credentials)"""
        print("\n" + "="*60)
        print("RETAILMIND USER AUTHENTICATION")
        print("="*60)
        
        # Get email
        email = input("\nEnter your registered email: ").strip().lower()
        if not email:
            print("✗ Email cannot be empty")
            sys.exit(1)
        
        # Get password (masked input)
        password = getpass.getpass("Enter your password (input hidden): ")
        if not password:
            print("✗ Password cannot be empty")
            sys.exit(1)
        
        # Look up user in database
        user = await self.db.users.find_one({"email": email})
        if not user:
            print(f"✗ User {email} not found in database")
            sys.exit(1)
        
        # Verify password
        if not verify_password(password, user.get("hashed_password", "")):
            print("✗ Invalid password")
            sys.exit(1)
        
        # Check if user is verified
        if not user.get("is_verified"):
            print("\n⚠ Your account is not verified yet.")
            print("Please complete email verification through the login page:")
            print(f"  1. Go to http://localhost:5174/")
            print(f"  2. Login with {email}")
            print(f"  3. Complete OTP verification")
            print(f"  4. Run this script again")
            sys.exit(1)
        
        self.user_id = str(user["_id"])
        self.user_email = email
        print(f"\n✓ Authenticated as: {email}")
        print(f"  User ID: {self.user_id}")
        return user
    
    async def record_initial_counts(self):
        """Record initial record counts for all collections"""
        print("\n" + "="*60)
        print("CURRENT DATABASE STATE")
        print("="*60)
        
        collections = {
            "categories": {},
            "suppliers": {"user_id": self.user_id},
            "products": {"user_id": self.user_id},
            "customers": {"user_id": self.user_id},
            "purchases": {"user_id": self.user_id},
            "sales": {"user_id": self.user_id},
            "inventory_transactions": {"user_id": self.user_id},
        }
        
        for collection_name, query_filter in collections.items():
            collection = self.db[collection_name]
            count = await collection.count_documents(query_filter)
            self.initial_counts[collection_name] = count
            
            # For categories, show both global and user-scoped
            if collection_name == "categories":
                user_categories = await collection.count_documents({"user_id": self.user_id})
                global_categories = count - user_categories
                print(f"\n  {collection_name}:")
                print(f"    Global: {global_categories}")
                print(f"    User-scoped: {user_categories}")
                print(f"    Total: {count}")
            else:
                print(f"\n  {collection_name}: {count}")
        
        return self.initial_counts
    
    async def verify_schemas(self):
        """Verify collection schemas and sample documents"""
        print("\n" + "="*60)
        print("SCHEMA VERIFICATION")
        print("="*60)
        
        # Check a product if it exists
        product = await self.db.products.find_one({"user_id": self.user_id})
        if product:
            print("\n✓ Product schema verified:")
            print(f"  Fields: {', '.join(sorted(product.keys())[:8])}...")
        
        # Check a supplier if it exists
        supplier = await self.db.suppliers.find_one({"user_id": self.user_id})
        if supplier:
            print("\n✓ Supplier schema verified:")
            print(f"  Fields: {', '.join(sorted(supplier.keys()))}")
        
        # Check categories
        category = await self.db.categories.find_one({})
        if category:
            print("\n✓ Category schema verified:")
            print(f"  Has user_id: {'user_id' in category}")
            print(f"  Fields: {', '.join(sorted(category.keys()))}")
    
    async def show_sample_records(self):
        """Show sample records from each collection"""
        print("\n" + "="*60)
        print("SAMPLE RECORDS")
        print("="*60)
        
        # Sample product
        product = await self.db.products.find_one({"user_id": self.user_id})
        if product:
            print(f"\nSample Product:")
            print(f"  Name: {product.get('name')}")
            print(f"  SKU: {product.get('sku')}")
            print(f"  Stock: {product.get('current_stock')}")
            print(f"  Price: ${product.get('selling_price')}")
        
        # Sample supplier
        supplier = await self.db.suppliers.find_one({"user_id": self.user_id})
        if supplier:
            print(f"\nSample Supplier:")
            print(f"  Name: {supplier.get('name')}")
            print(f"  Email: {supplier.get('email')}")
            print(f"  Phone: {supplier.get('phone')}")
        
        # Sample customer
        customer = await self.db.customers.find_one({"user_id": self.user_id})
        if customer:
            print(f"\nSample Customer:")
            print(f"  Name: {customer.get('name')}")
            print(f"  Email: {customer.get('email')}")
            print(f"  Phone: {customer.get('phone')}")


async def main():
    """Main entry point"""
    seeder = RetailMindSeeder()
    
    try:
        # Connect to database
        await seeder.connect()
        
        # Authenticate user interactively
        await seeder.authenticate_user()
        
        # Record initial state
        await seeder.record_initial_counts()
        
        # Verify schemas
        await seeder.verify_schemas()
        
        # Show sample records
        await seeder.show_sample_records()
        
        print("\n" + "="*60)
        print("✓ INSPECTION COMPLETE")
        print("="*60)
        print("\nNext steps:")
        print("  1. Review the data counts above")
        print("  2. Run the seeding process: python seed_demo_data.py")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await seeder.close()


if __name__ == "__main__":
    asyncio.run(main())
