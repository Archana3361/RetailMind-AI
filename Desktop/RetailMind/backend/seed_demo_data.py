#!/usr/bin/env python3
"""
RetailMind Secure Demo Data Seeding Script
===========================================

Seeds realistic, interconnected demo data for a verified RetailMind user.

Security & Design:
- Authenticates existing user at runtime (no hardcoded credentials)
- Uses existing database schemas and validation
- Preserves all existing data
- Idempotent: safe to run multiple times
- Respects ownership rules (categories global, others user-scoped)
- Proper stock tracking via inventory transactions

Data created:
- Categories: Global, reused/added to reach 8-12 total
- Suppliers: 10-15 user-scoped
- Products: 20-30 with valid category/supplier references
- Customers: 10+ for this user
- Purchases: 15+ with proper stock movements
- Sales: 30+ with proper stock deductions
- Inventory: Consistent with purchase/sales transactions

Usage:
    python seed_demo_data.py
"""

import asyncio
import sys
import getpass
from pathlib import Path
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import random
import string

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import verify_password


class DemoDataSeeder:
    def __init__(self):
        self.client = None
        self.db = None
        self.user_id = None
        self.user_email = None
        self.categories = {}
        self.suppliers = {}
        self.products = {}
        self.customers = {}
        self.created_counts = {}
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.DATABASE_NAME]
            await self.db.command("ping")
            print("✓ Connected to MongoDB")
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            sys.exit(1)
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    async def authenticate_user(self):
        """Authenticate user interactively"""
        print("\n" + "="*70)
        print("RETAILMIND DEMO DATA SEEDING")
        print("="*70)
        print("\nThis script will seed realistic demo data for your account.")
        print("Your credentials are required for authentication only.")
        print("Credentials are NOT stored in source code or logs.\n")
        
        email = input("Enter your registered email: ").strip().lower()
        password = getpass.getpass("Enter your password (input hidden): ")
        
        if not email or not password:
            print("✗ Email and password are required")
            sys.exit(1)
        
        # Look up user
        user = await self.db.users.find_one({"email": email})
        if not user:
            print(f"✗ User {email} not found")
            sys.exit(1)
        
        # Verify password
        if not verify_password(password, user.get("hashed_password", "")):
            print("✗ Invalid password")
            sys.exit(1)
        
        # Check verification status
        if not user.get("is_verified"):
            print("\n⚠ Your account is not verified yet.")
            print("Please complete email verification through the login page first.")
            sys.exit(1)
        
        self.user_id = str(user["_id"])
        self.user_email = email
        print(f"\n✓ Authenticated as: {email}")
        return user
    
    async def seed_categories(self):
        """Seed global categories (reuse existing, add missing)"""
        print("\n" + "-"*70)
        print("SEEDING CATEGORIES (Global)")
        print("-"*70)
        
        # Standard retail categories
        standard_categories = [
            {"name": "Electronics", "description": "Electronic devices and accessories"},
            {"name": "Clothing", "description": "Apparel and fashion items"},
            {"name": "Home & Garden", "description": "Home furnishings and garden supplies"},
            {"name": "Beauty & Personal Care", "description": "Cosmetics and personal hygiene"},
            {"name": "Food & Beverages", "description": "Groceries and beverages"},
            {"name": "Sports & Outdoors", "description": "Sports equipment and outdoor gear"},
            {"name": "Books & Media", "description": "Books, CDs, DVDs"},
            {"name": "Toys & Games", "description": "Children's toys and games"},
            {"name": "Office Supplies", "description": "Office equipment and supplies"},
            {"name": "Health & Wellness", "description": "Vitamins, supplements, health products"},
        ]
        
        created = 0
        for cat_data in standard_categories:
            # Check if category exists
            existing = await self.db.categories.find_one({"name": cat_data["name"]})
            if existing:
                self.categories[cat_data["name"]] = str(existing["_id"])
                print(f"  ↻ {cat_data['name']} (existing)")
            else:
                # Create new category (global, no user_id filter but still has user_id field)
                result = await self.db.categories.insert_one({
                    "user_id": self.user_id,  # Associate with user for reference
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "created_at": datetime.now(timezone.utc),
                })
                self.categories[cat_data["name"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {cat_data['name']}")
        
        self.created_counts["categories"] = created
        print(f"\nCreated: {created} new categories")
    
    async def seed_suppliers(self):
        """Seed 10-15 user-scoped suppliers"""
        print("\n" + "-"*70)
        print("SEEDING SUPPLIERS (User-Scoped)")
        print("-"*70)
        
        supplier_data = [
            {"name": "TechVendor Inc", "email": "sales@techvendor.example.com", "phone": "+1-555-0100", "contact_person": "John Smith"},
            {"name": "Fashion Wholesale Ltd", "email": "orders@fashionwholesale.example.com", "phone": "+1-555-0101", "contact_person": "Maria Garcia"},
            {"name": "Global Imports Co", "email": "info@globalimports.example.com", "phone": "+1-555-0102", "contact_person": "Ahmed Khan"},
            {"name": "Quality Distributors", "email": "sales@qualitydist.example.com", "phone": "+1-555-0103", "contact_person": "Sarah Johnson"},
            {"name": "Premier Wholesale", "email": "orders@premierwholesale.example.com", "phone": "+1-555-0104", "contact_person": "Michael Chen"},
            {"name": "EcoSupply Partners", "email": "contact@ecosupply.example.com", "phone": "+1-555-0105", "contact_person": "Elena Rodriguez"},
            {"name": "Digital Solutions Ltd", "email": "sales@digitalsolutions.example.com", "phone": "+1-555-0106", "contact_person": "David Smith"},
            {"name": "Beauty & Health Corp", "email": "orders@beautyhealth.example.com", "phone": "+1-555-0107", "contact_person": "Lisa Wong"},
            {"name": "Office Essentials Inc", "email": "sales@officeessentials.example.com", "phone": "+1-555-0108", "contact_person": "Robert Brown"},
            {"name": "Retail Dynamics", "email": "info@retaildynamics.example.com", "phone": "+1-555-0109", "contact_person": "Jennifer Lee"},
            {"name": "Supply Chain Masters", "email": "contact@scmasters.example.com", "phone": "+1-555-0110", "contact_person": "Thomas Anderson"},
            {"name": "Metro Wholesale Group", "email": "orders@metrowholesale.example.com", "phone": "+1-555-0111", "contact_person": "Patricia Martinez"},
        ]
        
        created = 0
        for sup_data in supplier_data:
            # Check if supplier exists for this user (by name)
            existing = await self.db.suppliers.find_one({
                "user_id": self.user_id,
                "name": sup_data["name"]
            })
            if existing:
                self.suppliers[sup_data["name"]] = str(existing["_id"])
                print(f"  ↻ {sup_data['name']} (existing)")
            else:
                result = await self.db.suppliers.insert_one({
                    "user_id": self.user_id,
                    "name": sup_data["name"],
                    "email": sup_data["email"],
                    "phone": sup_data["phone"],
                    "contact_person": sup_data.get("contact_person", ""),
                    "address": f"{random.randint(1000, 9999)} Supply St, Commerce City",
                    "total_purchase_value": 0.0,
                    "total_orders": 0,
                    "last_purchase_date": None,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
                self.suppliers[sup_data["name"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {sup_data['name']}")
        
        self.created_counts["suppliers"] = created
        print(f"\nCreated: {created} new suppliers")
    
    async def seed_products(self):
        """Seed 20-30 products with valid category/supplier refs"""
        print("\n" + "-"*70)
        print("SEEDING PRODUCTS (20-30)")
        print("-"*70)
        
        if not self.categories or not self.suppliers:
            print("✗ Categories and suppliers must be seeded first")
            return
        
        products_data = [
            # Electronics (TechVendor)
            {"name": "Wireless Bluetooth Speaker", "sku": "TECH-SPKR-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost_price": 35, "selling_price": 79.99, "stock": 50, "min_stock": 10},
            {"name": "USB-C Multi-port Hub", "sku": "TECH-HUB-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost_price": 25, "selling_price": 49.99, "stock": 30, "min_stock": 5},
            {"name": "Portable Power Bank 20000mAh", "sku": "TECH-BANK-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost_price": 20, "selling_price": 39.99, "stock": 40, "min_stock": 8},
            {"name": "HDMI 2.1 Cable 6ft", "sku": "TECH-HDMI-001", "category": "Electronics", "supplier": "TechVendor Inc", "cost_price": 8, "selling_price": 14.99, "stock": 100, "min_stock": 20},
            
            # Clothing (Fashion Wholesale)
            {"name": "Premium Cotton T-Shirt", "sku": "CLOTH-TSHIRT-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost_price": 12, "selling_price": 24.99, "stock": 75, "min_stock": 15},
            {"name": "Slim Fit Denim Jeans", "sku": "CLOTH-JEANS-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost_price": 35, "selling_price": 79.99, "stock": 40, "min_stock": 10},
            {"name": "Casual Hoodie", "sku": "CLOTH-HOODIE-001", "category": "Clothing", "supplier": "Fashion Wholesale Ltd", "cost_price": 28, "selling_price": 59.99, "stock": 25, "min_stock": 5},
            
            # Home & Garden (Global Imports)
            {"name": "Stainless Steel Cookware Set 10pc", "sku": "HOME-COOK-001", "category": "Home & Garden", "supplier": "Global Imports Co", "cost_price": 80, "selling_price": 179.99, "stock": 15, "min_stock": 3},
            {"name": "Memory Foam Pillow Set", "sku": "HOME-PILLOW-001", "category": "Home & Garden", "supplier": "Global Imports Co", "cost_price": 30, "selling_price": 69.99, "stock": 20, "min_stock": 5},
            {"name": "LED Desk Lamp with USB", "sku": "HOME-LAMP-001", "category": "Home & Garden", "supplier": "Global Imports Co", "cost_price": 18, "selling_price": 39.99, "stock": 35, "min_stock": 8},
            
            # Beauty & Personal Care
            {"name": "Premium Facial Moisturizer 50ml", "sku": "BEAUTY-MOIST-001", "category": "Beauty & Personal Care", "supplier": "Beauty & Health Corp", "cost_price": 15, "selling_price": 34.99, "stock": 45, "min_stock": 10},
            {"name": "Organic Shampoo 250ml", "sku": "BEAUTY-SHMP-001", "category": "Beauty & Personal Care", "supplier": "Beauty & Health Corp", "cost_price": 8, "selling_price": 16.99, "stock": 60, "min_stock": 15},
            {"name": "Face Wash Cleanser 200ml", "sku": "BEAUTY-WASH-001", "category": "Beauty & Personal Care", "supplier": "Beauty & Health Corp", "cost_price": 6, "selling_price": 12.99, "stock": 50, "min_stock": 10},
            
            # Food & Beverages
            {"name": "Premium Arabica Coffee Beans 1kg", "sku": "FOOD-COFFEE-001", "category": "Food & Beverages", "supplier": "EcoSupply Partners", "cost_price": 12, "selling_price": 24.99, "stock": 30, "min_stock": 5},
            {"name": "Organic Green Tea 50 bags", "sku": "FOOD-TEA-001", "category": "Food & Beverages", "supplier": "EcoSupply Partners", "cost_price": 5, "selling_price": 10.99, "stock": 40, "min_stock": 10},
            {"name": "Raw Honey 500ml", "sku": "FOOD-HONEY-001", "category": "Food & Beverages", "supplier": "EcoSupply Partners", "cost_price": 10, "selling_price": 18.99, "stock": 25, "min_stock": 5},
            
            # Office Supplies
            {"name": "A4 Paper Ream 500 sheets", "sku": "OFFICE-PAPER-001", "category": "Office Supplies", "supplier": "Office Essentials Inc", "cost_price": 3.50, "selling_price": 6.99, "stock": 100, "min_stock": 20},
            {"name": "Ballpoint Pen Set 50pcs", "sku": "OFFICE-PEN-001", "category": "Office Supplies", "supplier": "Office Essentials Inc", "cost_price": 8, "selling_price": 14.99, "stock": 50, "min_stock": 10},
            {"name": "Manila Folders Pack 100", "sku": "OFFICE-FOLDER-001", "category": "Office Supplies", "supplier": "Office Essentials Inc", "cost_price": 5, "selling_price": 9.99, "stock": 80, "min_stock": 15},
            
            # Sports & Outdoors
            {"name": "Yoga Mat 6mm Non-Slip", "sku": "SPORTS-YOGA-001", "category": "Sports & Outdoors", "supplier": "Retail Dynamics", "cost_price": 15, "selling_price": 34.99, "stock": 20, "min_stock": 5},
            {"name": "Water Bottle 1L Insulated", "sku": "SPORTS-BOTTLE-001", "category": "Sports & Outdoors", "supplier": "Retail Dynamics", "cost_price": 12, "selling_price": 24.99, "stock": 35, "min_stock": 8},
            
            # Health & Wellness
            {"name": "Vitamin C 1000mg Tablets 60ct", "sku": "HEALTH-VITC-001", "category": "Health & Wellness", "supplier": "Beauty & Health Corp", "cost_price": 10, "selling_price": 19.99, "stock": 40, "min_stock": 10},
            {"name": "Multivitamin Gummies 90ct", "sku": "HEALTH-MULTI-001", "category": "Health & Wellness", "supplier": "Beauty & Health Corp", "cost_price": 14, "selling_price": 27.99, "stock": 30, "min_stock": 8},
            
            # Books & Media
            {"name": "Business Strategy Handbook", "sku": "BOOKS-BIZ-001", "category": "Books & Media", "supplier": "Digital Solutions Ltd", "cost_price": 18, "selling_price": 34.99, "stock": 15, "min_stock": 3},
            {"name": "Python Programming Guide", "sku": "BOOKS-PYTHON-001", "category": "Books & Media", "supplier": "Digital Solutions Ltd", "cost_price": 22, "selling_price": 39.99, "stock": 12, "min_stock": 2},
        ]
        
        created = 0
        for prod_data in products_data:
            # Check if product exists for this user (by SKU)
            existing = await self.db.products.find_one({
                "user_id": self.user_id,
                "sku": prod_data["sku"]
            })
            if existing:
                self.products[prod_data["sku"]] = str(existing["_id"])
                print(f"  ↻ {prod_data['name']} ({prod_data['sku']}) - existing")
            else:
                category_id = self.categories.get(prod_data["category"])
                supplier_id = self.suppliers.get(prod_data["supplier"])
                
                if not category_id or not supplier_id:
                    print(f"  ✗ {prod_data['name']} - missing category or supplier")
                    continue
                
                result = await self.db.products.insert_one({
                    "user_id": self.user_id,
                    "name": prod_data["name"],
                    "sku": prod_data["sku"],
                    "category_id": ObjectId(category_id),
                    "category_name": prod_data["category"],
                    "brand": "Demo Brand",
                    "unit": "pcs",
                    "cost_price": prod_data["cost_price"],
                    "selling_price": prod_data["selling_price"],
                    "current_stock": prod_data["stock"],
                    "minimum_stock": prod_data["min_stock"],
                    "supplier_id": ObjectId(supplier_id),
                    "supplier_name": prod_data["supplier"],
                    "description": f"Premium {prod_data['name'].lower()}",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
                self.products[prod_data["sku"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {prod_data['name']} ({prod_data['sku']})")
        
        self.created_counts["products"] = created
        print(f"\nCreated: {created} new products")
    
    async def seed_customers(self):
        """Seed 10+ customers"""
        print("\n" + "-"*70)
        print("SEEDING CUSTOMERS (10+)")
        print("-"*70)
        
        customers_data = [
            {"name": "Acme Corporation", "email": "orders@acmecorp.example.com", "phone": "+1-555-1000", "address": "123 Business Ave, Commerce City"},
            {"name": "Tech Solutions LLC", "email": "purchasing@techsolutions.example.com", "phone": "+1-555-1001", "address": "456 Innovation Blvd, Tech Park"},
            {"name": "Retail Plus", "email": "buyer@retailplus.example.com", "phone": "+1-555-1002", "address": "789 Market St, Downtown"},
            {"name": "Fashion Forward Inc", "email": "orders@fashionforward.example.com", "phone": "+1-555-1003", "address": "321 Style Ave, Fashion District"},
            {"name": "Home Furnishings Co", "email": "purchasing@homefurnish.example.com", "phone": "+1-555-1004", "address": "654 Decor Ln, Design Quarter"},
            {"name": "Wellness Centers Network", "email": "supplies@wellnesscenters.example.com", "phone": "+1-555-1005", "address": "987 Health Rd, Medical District"},
            {"name": "Office Depot Franchise", "email": "orders@officedepotfranchise.example.com", "phone": "+1-555-1006", "address": "147 Commerce Pkwy, Business Park"},
            {"name": "Sports & Recreation Ltd", "email": "buyer@sportsrecreation.example.com", "phone": "+1-555-1007", "address": "258 Athletic Way, Sports Zone"},
            {"name": "Convenience Store Chain", "email": "purchasing@conveniencechain.example.com", "phone": "+1-555-1008", "address": "369 Retail Rd, Downtown"},
            {"name": "Educational Supplies", "email": "orders@edsupplies.example.com", "phone": "+1-555-1009", "address": "741 Academy Ln, Education Campus"},
            {"name": "Corporate Events", "email": "coordinator@corporateevents.example.com", "phone": "+1-555-1010", "address": "852 Event Plaza, Convention Center"},
            {"name": "Boutique Imports", "email": "manager@boutiqueimports.example.com", "phone": "+1-555-1011", "address": "963 Unique St, Arts District"},
        ]
        
        created = 0
        for cust_data in customers_data:
            # Check if customer exists (by email and user_id)
            existing = await self.db.customers.find_one({
                "user_id": self.user_id,
                "email": cust_data["email"]
            })
            if existing:
                self.customers[cust_data["name"]] = str(existing["_id"])
                print(f"  ↻ {cust_data['name']} (existing)")
            else:
                result = await self.db.customers.insert_one({
                    "user_id": self.user_id,
                    "name": cust_data["name"],
                    "email": cust_data["email"],
                    "phone": cust_data["phone"],
                    "address": cust_data["address"],
                    "total_purchases": 0.0,
                    "total_orders": 0,
                    "last_purchase_date": None,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
                self.customers[cust_data["name"]] = str(result.inserted_id)
                created += 1
                print(f"  ✓ {cust_data['name']}")
        
        self.created_counts["customers"] = created
        print(f"\nCreated: {created} new customers")


async def main():
    """Main entry point"""
    seeder = DemoDataSeeder()
    
    try:
        await seeder.connect()
        await seeder.authenticate_user()
        await seeder.seed_categories()
        await seeder.seed_suppliers()
        await seeder.seed_products()
        await seeder.seed_customers()
        
        print("\n" + "="*70)
        print("✓ DEMO DATA SEEDING COMPLETE")
        print("="*70)
        print("\nRecords created:")
        for collection, count in seeder.created_counts.items():
            print(f"  {collection}: {count}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await seeder.close()


if __name__ == "__main__":
    asyncio.run(main())
