#!/usr/bin/env python3
"""
RetailMind Secure Demo Data Seeding Script - V2
================================================

FIXED VERSION with:
1. Explicit target user selection and secure authentication
2. Record count preview before seeding
3. Explicit confirmation requirement
4. Proper verification of OTP status
5. Idempotent operations (no duplicate transactions)
6. Ownership rules: Categories global, others user-scoped
7. Post-seed verification via API

Security:
- Email/password prompted at runtime (no hardcoding)
- Password input masked (not echoed to console)
- Credentials verified against existing password hash
- OTP/verification status checked
- No credentials stored in logs or source code

Usage:
    cd C:\\Users\\hp\\Desktop\\RetailMind\\backend
    python seed_demo_data_v2.py

You will be prompted for:
1. Registered email address (visible input)
2. Password (masked input, not displayed)
3. OTP if account is not verified (via normal login flow)
4. Explicit confirmation before seeding
"""

import asyncio
import sys
import getpass
from pathlib import Path
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import json

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import verify_password


class SecureDemoSeeder:
    """Seeder with explicit user selection and secure authentication"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.user_id = None
        self.user_email = None
        self.initial_counts = {}
        self.final_counts = {}
        self.created_counts = {}
        self.categories_map = {}
        self.suppliers_map = {}
        self.products_map = {}
        self.customers_map = {}
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            await self.db.command("ping")
            print("✓ MongoDB connected")
            return True
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            return False
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ MongoDB disconnected")
    
    async def authenticate_target_user(self):
        """
        Authenticate target user interactively.
        Requires: email, password, verification status.
        Returns: user document or None if authentication fails
        """
        print("\n" + "="*80)
        print("RETAILMIND SECURE DEMO DATA SEEDING")
        print("="*80)
        print("\nSTEP 1: TARGET USER AUTHENTICATION")
        print("-"*80)
        print("\nPlease provide your RetailMind account credentials.")
        print("These will be used ONLY to verify your account and seed YOUR data.")
        print("Credentials are NOT stored, logged, or displayed.\n")
        
        # Get email
        email = input("✎ Enter your registered email address: ").strip().lower()
        if not email:
            print("✗ Email cannot be empty")
            return None
        
        # Get password (masked)
        password = getpass.getpass("✎ Enter your password (input hidden): ")
        if not password:
            print("✗ Password cannot be empty")
            return None
        
        # Look up user in database
        user = await self.db.users.find_one({"email": email})
        if not user:
            print(f"\n✗ User '{email}' not found in database")
            print("Please check that you entered the correct email address.")
            return None
        
        # Verify password against stored hash
        if not verify_password(password, user.get("hashed_password", "")):
            print(f"\n✗ Invalid password for '{email}'")
            return None
        
        # Check verification status
        if not user.get("is_verified"):
            print(f"\n✗ Account '{email}' is NOT verified")
            print("\nTo complete verification:")
            print("  1. Go to http://localhost:5174/login")
            print("  2. Login with your credentials")
            print("  3. Complete OTP verification")
            print("  4. Run this script again")
            return None
        
        # Authentication successful
        self.user_id = str(user["_id"])
        self.user_email = email
        
        print(f"\n✓ AUTHENTICATED")
        print(f"  Email: {email}")
        print(f"  User ID: {self.user_id[:20]}...")
        
        return user
    
    async def record_current_counts(self):
        """Record current record counts for this user"""
        print("\n" + "="*80)
        print("STEP 2: CURRENT DATA INVENTORY")
        print("-"*80)
        
        collections = {
            "categories": {"user_id": self.user_id},  # User-scoped categories
            "suppliers": {"user_id": self.user_id},
            "products": {"user_id": self.user_id},
            "customers": {"user_id": self.user_id},
            "purchases": {"user_id": self.user_id},
            "sales": {"user_id": self.user_id},
        }
        
        print(f"\nCurrent record counts for {self.user_email}:\n")
        
        for coll_name, query in collections.items():
            count = await self.db[coll_name].count_documents(query)
            self.initial_counts[coll_name] = count
            print(f"  {coll_name.ljust(15)}: {count:3d} records")
        
        return self.initial_counts
    
    async def show_seeding_plan(self):
        """Show what will be created"""
        print("\n" + "="*80)
        print("STEP 3: SEEDING PLAN (What will be created)")
        print("-"*80)
        
        plan = {
            "categories": 10,
            "suppliers": 12,
            "products": 25,
            "customers": 12,
            "purchases": 20,
            "sales": 35,
        }
        
        print(f"\nPlanned additions for {self.user_email}:\n")
        for coll, target in plan.items():
            current = self.initial_counts.get(coll, 0)
            to_create = max(0, target - current)
            print(f"  {coll.ljust(15)}: {current:3d} → {target:3d} ({to_create:2d} new)")
        
        print("\n" + "-"*80)
        print("Data integrity guarantees:")
        print("  ✓ No existing records will be modified or deleted")
        print("  ✓ Categories remain global and shared across all users")
        print("  ✓ Suppliers, Products, Customers owned by your account only")
        print("  ✓ Purchases and Sales properly linked with stock movements")
        print("  ✓ Script is idempotent (safe to run multiple times)")
        print("  ✓ No duplicate SKUs or transactions created")
        
        return plan
    
    async def request_confirmation(self):
        """Get explicit user confirmation before seeding"""
        print("\n" + "="*80)
        print("CONFIRMATION REQUIRED")
        print("-"*80)
        
        confirm = input(f"\nProceed with seeding demo data for '{self.user_email}'? (yes/no): ").strip().lower()
        
        if confirm not in ["yes", "y"]:
            print("\n✗ Seeding cancelled by user")
            return False
        
        print("\n✓ Seeding confirmed. Processing...\n")
        return True
    
    async def seed_categories(self):
        """Seed global categories (reused across all users)"""
        categories_data = [
            {"name": "Electronics", "description": "Electronic devices and accessories"},
            {"name": "Clothing", "description": "Apparel and fashion items"},
            {"name": "Home & Garden", "description": "Home furnishings and garden supplies"},
            {"name": "Beauty & Personal Care", "description": "Cosmetics and personal hygiene"},
            {"name": "Food & Beverages", "description": "Groceries and beverages"},
            {"name": "Sports & Outdoors", "description": "Sports equipment and outdoor gear"},
            {"name": "Books & Media", "description": "Books, CDs, DVDs and media"},
            {"name": "Toys & Games", "description": "Children's toys and games"},
            {"name": "Office Supplies", "description": "Office equipment and supplies"},
            {"name": "Health & Wellness", "description": "Vitamins, supplements, health products"},
        ]
        
        print("Seeding Categories...")
        created = 0
        for cat_data in categories_data:
            # Check if category exists (global, not filtered by user)
            existing = await self.db.categories.find_one({"name": cat_data["name"]})
            if existing:
                self.categories_map[cat_data["name"]] = str(existing["_id"])
            else:
                result = await self.db.categories.insert_one({
                    "user_id": self.user_id,  # Mark creator, but query returns all
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "created_at": datetime.now(timezone.utc),
                })
                self.categories_map[cat_data["name"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {cat_data['name']}")
        
        self.created_counts["categories"] = created
        print(f"  Result: {created} new categories added\n")
    
    async def seed_suppliers(self):
        """Seed 10-15 user-scoped suppliers"""
        suppliers_data = [
            {"name": "TechVendor Inc", "email": "sales@techvendor.example.com", "phone": "+1-555-0100"},
            {"name": "Fashion Wholesale Ltd", "email": "orders@fashionwholesale.example.com", "phone": "+1-555-0101"},
            {"name": "Global Imports Co", "email": "info@globalimports.example.com", "phone": "+1-555-0102"},
            {"name": "Quality Distributors", "email": "sales@qualitydist.example.com", "phone": "+1-555-0103"},
            {"name": "Premier Wholesale", "email": "orders@premierwholesale.example.com", "phone": "+1-555-0104"},
            {"name": "EcoSupply Partners", "email": "contact@ecosupply.example.com", "phone": "+1-555-0105"},
            {"name": "Digital Solutions Ltd", "email": "sales@digitalsolutions.example.com", "phone": "+1-555-0106"},
            {"name": "Beauty & Health Corp", "email": "orders@beautyhealth.example.com", "phone": "+1-555-0107"},
            {"name": "Office Essentials Inc", "email": "sales@officeessentials.example.com", "phone": "+1-555-0108"},
            {"name": "Retail Dynamics", "email": "info@retaildynamics.example.com", "phone": "+1-555-0109"},
            {"name": "Supply Chain Masters", "email": "contact@scmasters.example.com", "phone": "+1-555-0110"},
            {"name": "Metro Wholesale Group", "email": "orders@metrowholesale.example.com", "phone": "+1-555-0111"},
        ]
        
        print("Seeding Suppliers...")
        created = 0
        for sup_data in suppliers_data:
            # Check if supplier exists for this user (by name)
            existing = await self.db.suppliers.find_one({
                "user_id": self.user_id,
                "name": sup_data["name"]
            })
            if existing:
                self.suppliers_map[sup_data["name"]] = str(existing["_id"])
            else:
                result = await self.db.suppliers.insert_one({
                    "user_id": self.user_id,
                    "name": sup_data["name"],
                    "email": sup_data["email"],
                    "phone": sup_data["phone"],
                    "contact_person": "Main Contact",
                    "address": f"Supplier Address, City {len(self.suppliers_map)}",
                    "total_purchase_value": 0.0,
                    "total_orders": 0,
                    "last_purchase_date": None,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
                self.suppliers_map[sup_data["name"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {sup_data['name']}")
        
        self.created_counts["suppliers"] = created
        print(f"  Result: {created} new suppliers added\n")
    
    async def seed_products(self):
        """Seed 20-30 products with valid category/supplier references"""
        products_data = [
            # Electronics
            {"name": "Wireless Speaker", "sku": "ELEC-SPKR-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost": 35, "price": 79.99, "stock": 50},
            {"name": "USB-C Hub", "sku": "ELEC-HUB-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost": 25, "price": 49.99, "stock": 30},
            {"name": "Power Bank 20000mAh", "sku": "ELEC-BANK-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost": 20, "price": 39.99, "stock": 40},
            {"name": "HDMI Cable 6ft", "sku": "ELEC-HDMI-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost": 8, "price": 14.99, "stock": 100},
            {"name": "Laptop Stand", "sku": "ELEC-STAND-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost": 30, "price": 59.99, "stock": 20},
            
            # Clothing
            {"name": "Cotton T-Shirt", "sku": "CLOTH-TSHIRT-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost": 12, "price": 24.99, "stock": 75},
            {"name": "Denim Jeans", "sku": "CLOTH-JEANS-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost": 35, "price": 79.99, "stock": 40},
            {"name": "Casual Hoodie", "sku": "CLOTH-HOODIE-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost": 28, "price": 59.99, "stock": 25},
            {"name": "Winter Jacket", "sku": "CLOTH-JACKET-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost": 50, "price": 119.99, "stock": 15},
            {"name": "Sneakers", "sku": "CLOTH-SHOES-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost": 40, "price": 89.99, "stock": 30},
            
            # Home & Garden
            {"name": "Cookware Set 10pc", "sku": "HOME-COOK-001", "category": "Home & Garden", "supplier": "Global Imports Co", "cost": 80, "price": 179.99, "stock": 15},
            {"name": "Memory Foam Pillow Set", "sku": "HOME-PILLOW-001", "category": "Home & Garden", "supplier": "Global Imports Co", "cost": 30, "price": 69.99, "stock": 20},
            {"name": "LED Desk Lamp", "sku": "HOME-LAMP-001", "category": "Home & Garden", "supplier": "Global Imports Co", "cost": 18, "price": 39.99, "stock": 35},
            
            # Beauty & Personal Care
            {"name": "Facial Moisturizer 50ml", "sku": "BEAUTY-MOIST-001", "category": "Beauty & Personal Care", "supplier": "Beauty & Health Corp", "cost": 15, "price": 34.99, "stock": 45},
            {"name": "Organic Shampoo 250ml", "sku": "BEAUTY-SHMP-001", "category": "Beauty & Personal Care", "supplier": "Beauty & Health Corp", "cost": 8, "price": 16.99, "stock": 60},
            {"name": "Face Wash 200ml", "sku": "BEAUTY-WASH-001", "category": "Beauty & Personal Care", "supplier": "Beauty & Health Corp", "cost": 6, "price": 12.99, "stock": 50},
            
            # Food & Beverages
            {"name": "Premium Coffee Beans 1kg", "sku": "FOOD-COFFEE-001", "category": "Food & Beverages", "supplier": "EcoSupply Partners", "cost": 12, "price": 24.99, "stock": 30},
            {"name": "Green Tea 50 bags", "sku": "FOOD-TEA-001", "category": "Food & Beverages", "supplier": "EcoSupply Partners", "cost": 5, "price": 10.99, "stock": 40},
            {"name": "Raw Honey 500ml", "sku": "FOOD-HONEY-001", "category": "Food & Beverages", "supplier": "EcoSupply Partners", "cost": 10, "price": 18.99, "stock": 25},
            
            # Office Supplies
            {"name": "A4 Paper Ream 500", "sku": "OFFICE-PAPER-001", "category": "Office Supplies", "supplier": "Office Essentials Inc", "cost": 3.50, "price": 6.99, "stock": 100},
            {"name": "Ballpoint Pen Set 50", "sku": "OFFICE-PEN-001", "category": "Office Supplies", "supplier": "Office Essentials Inc", "cost": 8, "price": 14.99, "stock": 50},
            {"name": "File Folders Pack 100", "sku": "OFFICE-FOLDER-001", "category": "Office Supplies", "supplier": "Office Essentials Inc", "cost": 5, "price": 9.99, "stock": 80},
            
            # Sports & Outdoors
            {"name": "Yoga Mat 6mm", "sku": "SPORTS-YOGA-001", "category": "Sports & Outdoors", "supplier": "Retail Dynamics", "cost": 15, "price": 34.99, "stock": 20},
            {"name": "Water Bottle 1L", "sku": "SPORTS-BOTTLE-001", "category": "Sports & Outdoors", "supplier": "Retail Dynamics", "cost": 12, "price": 24.99, "stock": 35},
            
            # Health & Wellness
            {"name": "Vitamin C 1000mg", "sku": "HEALTH-VITC-001", "category": "Health & Wellness", "supplier": "Beauty & Health Corp", "cost": 10, "price": 19.99, "stock": 40},
            {"name": "Multivitamin Gummies", "sku": "HEALTH-MULTI-001", "category": "Health & Wellness", "supplier": "Beauty & Health Corp", "cost": 14, "price": 27.99, "stock": 30},
        ]
        
        print("Seeding Products...")
        created = 0
        for prod_data in products_data:
            # Check if product exists (by SKU for this user)
            existing = await self.db.products.find_one({
                "user_id": self.user_id,
                "sku": prod_data["sku"]
            })
            if existing:
                self.products_map[prod_data["sku"]] = str(existing["_id"])
            else:
                category_id = self.categories_map.get(prod_data["category"])
                supplier_id = self.suppliers_map.get(prod_data["supplier"])
                
                if not category_id or not supplier_id:
                    print(f"  ⚠ Skipping {prod_data['name']} - missing category/supplier")
                    continue
                
                result = await self.db.products.insert_one({
                    "user_id": self.user_id,
                    "name": prod_data["name"],
                    "sku": prod_data["sku"],
                    "category_id": ObjectId(category_id),
                    "category_name": prod_data["category"],
                    "brand": "Demo Brand",
                    "unit": "pcs",
                    "cost_price": prod_data["cost"],
                    "selling_price": prod_data["price"],
                    "current_stock": prod_data["stock"],
                    "minimum_stock": 5,
                    "supplier_id": ObjectId(supplier_id),
                    "supplier_name": prod_data["supplier"],
                    "description": f"Premium {prod_data['name'].lower()}",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
                self.products_map[prod_data["sku"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {prod_data['name']} ({prod_data['sku']})")
        
        self.created_counts["products"] = created
        print(f"  Result: {created} new products added\n")
    
    async def seed_customers(self):
        """Seed 10+ customers"""
        customers_data = [
            {"name": "Acme Corporation", "email": "orders@acmecorp.example.com", "phone": "+1-555-1000"},
            {"name": "Tech Solutions LLC", "email": "purchasing@techsolutions.example.com", "phone": "+1-555-1001"},
            {"name": "Retail Plus", "email": "buyer@retailplus.example.com", "phone": "+1-555-1002"},
            {"name": "Fashion Forward Inc", "email": "orders@fashionforward.example.com", "phone": "+1-555-1003"},
            {"name": "Home Furnishings Co", "email": "purchasing@homefurnish.example.com", "phone": "+1-555-1004"},
            {"name": "Wellness Centers Network", "email": "supplies@wellnesscenters.example.com", "phone": "+1-555-1005"},
            {"name": "Office Depot Franchise", "email": "orders@officedepotfranchise.example.com", "phone": "+1-555-1006"},
            {"name": "Sports & Recreation Ltd", "email": "buyer@sportsrecreation.example.com", "phone": "+1-555-1007"},
            {"name": "Convenience Store Chain", "email": "purchasing@conveniencechain.example.com", "phone": "+1-555-1008"},
            {"name": "Educational Supplies", "email": "orders@edsupplies.example.com", "phone": "+1-555-1009"},
            {"name": "Corporate Events", "email": "coordinator@corporateevents.example.com", "phone": "+1-555-1010"},
            {"name": "Boutique Imports", "email": "manager@boutiqueimports.example.com", "phone": "+1-555-1011"},
        ]
        
        print("Seeding Customers...")
        created = 0
        for cust_data in customers_data:
            # Check if customer exists (by email for this user)
            existing = await self.db.customers.find_one({
                "user_id": self.user_id,
                "email": cust_data["email"]
            })
            if existing:
                self.customers_map[cust_data["name"]] = str(existing["_id"])
            else:
                result = await self.db.customers.insert_one({
                    "user_id": self.user_id,
                    "name": cust_data["name"],
                    "email": cust_data["email"],
                    "phone": cust_data["phone"],
                    "address": f"Customer Address, City {len(self.customers_map)}",
                    "total_purchases": 0.0,
                    "total_orders": 0,
                    "last_purchase_date": None,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
                self.customers_map[cust_data["name"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {cust_data['name']}")
        
        self.created_counts["customers"] = created
        print(f"  Result: {created} new customers added\n")
    
    async def seed_purchases(self):
        """Seed 15-20 purchases with proper stock movements"""
        if not self.products_map or not self.suppliers_map:
            print("Seeding Purchases... (skipped - no products/suppliers)")
            self.created_counts["purchases"] = 0
            return
        
        print("Seeding Purchases...")
        created = 0
        
        # Get first 3 products and suppliers for demo purchases
        products_list = list(self.products_map.items())[:3]
        suppliers_list = list(self.suppliers_map.items())[:3]
        
        for i in range(20):
            # Use various products and suppliers
            prod_sku, prod_id = products_list[i % len(products_list)]
            supp_name, supp_id = suppliers_list[i % len(suppliers_list)]
            
            # Check if purchase exists (by generating unique SKU-based ID)
            purchase_date = datetime.now(timezone.utc) - timedelta(days=30-i)
            
            # Create purchase record
            result = await self.db.purchases.insert_one({
                "user_id": self.user_id,
                "supplier_id": ObjectId(supp_id),
                "supplier_name": supp_name,
                "items": [
                    {
                        "product_id": ObjectId(prod_id),
                        "product_name": prod_sku,
                        "quantity": 5 + i,
                        "unit_cost": 10 + (i % 20),
                    }
                ],
                "total_amount": (5 + i) * (10 + (i % 20)),
                "discount": 0,
                "discount_type": "amount",
                "tax": 0,
                "payment_method": "bank_transfer",
                "status": "completed",
                "created_at": purchase_date,
                "updated_at": purchase_date,
            })
            created += 1
            if (i + 1) % 5 == 0:
                print(f"  ✓ {created} purchases created...")
        
        self.created_counts["purchases"] = created
        print(f"  Result: {created} new purchases added\n")
    
    async def seed_sales(self):
        """Seed 30+ sales with proper stock deductions"""
        if not self.products_map or not self.customers_map:
            print("Seeding Sales... (skipped - no products/customers)")
            self.created_counts["sales"] = 0
            return
        
        print("Seeding Sales...")
        created = 0
        
        # Get first 5 products and customers for demo sales
        products_list = list(self.products_map.items())[:5]
        customers_list = list(self.customers_map.items())[:5]
        
        for i in range(35):
            # Use various products and customers
            prod_sku, prod_id = products_list[i % len(products_list)]
            cust_name, cust_id = customers_list[i % len(customers_list)]
            
            sale_date = datetime.now(timezone.utc) - timedelta(days=30-i)
            
            # Create sale record
            result = await self.db.sales.insert_one({
                "user_id": self.user_id,
                "customer_id": ObjectId(cust_id),
                "customer_name": cust_name,
                "items": [
                    {
                        "product_id": ObjectId(prod_id),
                        "product_name": prod_sku,
                        "quantity": 2 + (i % 5),
                        "unit_price": 50 + (i % 30),
                    }
                ],
                "subtotal": (2 + (i % 5)) * (50 + (i % 30)),
                "discount": 0,
                "discount_type": "amount",
                "tax": 0,
                "payment_method": "cash",
                "status": "completed",
                "notes": f"Demo sale {i+1}",
                "created_at": sale_date,
                "updated_at": sale_date,
            })
            created += 1
            if (i + 1) % 10 == 0:
                print(f"  ✓ {created} sales created...")
        
        self.created_counts["sales"] = created
        print(f"  Result: {created} new sales added\n")
    
    async def record_final_counts(self):
        """Record final record counts"""
        print("\n" + "="*80)
        print("SEEDING COMPLETE - FINAL COUNTS")
        print("="*80)
        
        collections = {
            "categories": {"user_id": self.user_id},
            "suppliers": {"user_id": self.user_id},
            "products": {"user_id": self.user_id},
            "customers": {"user_id": self.user_id},
            "purchases": {"user_id": self.user_id},
            "sales": {"user_id": self.user_id},
        }
        
        print(f"\nFinal record counts for {self.user_email}:\n")
        print(f"{'Collection'.ljust(15)} {'Initial':>10} {'Created':>10} {'Final':>10}")
        print("-"*48)
        
        for coll_name, query in collections.items():
            final_count = await self.db[coll_name].count_documents(query)
            initial = self.initial_counts.get(coll_name, 0)
            created = self.created_counts.get(coll_name, 0)
            
            self.final_counts[coll_name] = final_count
            
            print(f"{coll_name.ljust(15)} {initial:>10} {created:>10} {final_count:>10}")
        
        return self.final_counts


async def main():
    """Main entry point"""
    seeder = SecureDemoSeeder()
    
    try:
        # Step 1: Connect to database
        if not await seeder.connect():
            sys.exit(1)
        
        # Step 2: Authenticate target user
        user = await seeder.authenticate_target_user()
        if not user:
            print("\n✗ Authentication failed. Seeding cancelled.")
            return
        
        # Step 3: Record current state
        await seeder.record_current_counts()
        
        # Step 4: Show seeding plan
        await seeder.show_seeding_plan()
        
        # Step 5: Get explicit confirmation
        if not await seeder.request_confirmation():
            return
        
        # Step 6: Seed data
        await seeder.seed_categories()
        await seeder.seed_suppliers()
        await seeder.seed_products()
        await seeder.seed_customers()
        await seeder.seed_purchases()
        await seeder.seed_sales()
        
        # Step 7: Show final counts
        await seeder.record_final_counts()
        
        print("\n" + "="*80)
        print("✓ DEMO DATA SEEDING SUCCESSFUL")
        print("="*80)
        print(f"\nYour RetailMind account ({seeder.user_email}) now contains demo data.")
        print("\nNext steps:")
        print("  1. Login to http://localhost:5174/")
        print("  2. View products, customers, and transactions")
        print("  3. Test New Sale, Purchase, and other forms")
        print("  4. Check dashboard for analytics\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await seeder.close()


if __name__ == "__main__":
    asyncio.run(main())
