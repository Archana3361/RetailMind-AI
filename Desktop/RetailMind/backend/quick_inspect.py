#!/usr/bin/env python3
"""Quick database inspection without authentication"""

import asyncio
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings


async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        await db.command("ping")
        print("✓ MongoDB connected\n")
        
        # List all users
        users = await db.users.find({}, {"email": 1, "_id": 1, "is_verified": 1}).to_list(None)
        print(f"Users in database ({len(users)}):")
        for u in users:
            verified = "✓" if u.get("is_verified") else "✗"
            print(f"  [{verified}] {u.get('email')} (ID: {str(u['_id'])[:12]}...)")
        
        # Show collection counts
        print("\nCollection counts:")
        for coll_name in ["categories", "products", "customers", "suppliers", "sales", "purchases"]:
            count = await db[coll_name].count_documents({})
            print(f"  {coll_name}: {count}")
        
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
