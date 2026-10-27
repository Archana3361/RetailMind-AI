#!/usr/bin/env python3
"""
Reset a demo account password in MongoDB.

This script uses the project's own password hashing function to securely
generate a bcrypt hash for a new password, then updates the MongoDB database.

Usage:
    python reset_demo_password.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.security import hash_password
from app.core.config import settings
from datetime import datetime, timezone


async def reset_demo_password(email: str, new_password: str):
    """Reset password for a user account."""
    
    print("\n" + "=" * 60)
    print("RETAILMIND DEMO PASSWORD RESET")
    print("=" * 60)
    
    # Connect to MongoDB
    print(f"\n[1/4] Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        await client.admin.command("ping")
        print(f"      ✓ Connected to: {settings.DATABASE_NAME}")
    except Exception as e:
        print(f"      ✗ Connection failed: {e}")
        client.close()
        return False
    
    # Find user
    print(f"\n[2/4] Checking if user exists: {email}")
    user = await db.users.find_one({"email": email.lower().strip()})
    
    if not user:
        print(f"      ✗ User not found")
        client.close()
        return False
    
    print(f"      ✓ User found: {user.get('full_name')}")
    print(f"      Shop: {user.get('shop_name')}")
    print(f"      Verified: {user.get('is_verified')}")
    
    # Hash new password
    print(f"\n[3/4] Hashing new password...")
    hashed_password = hash_password(new_password)
    print(f"      ✓ Password hashed with bcrypt (cost=12)")
    print(f"      Hash: {hashed_password[:50]}...")
    
    # Update database
    print(f"\n[4/4] Updating database...")
    result = await db.users.update_one(
        {"email": email.lower().strip()},
        {
            "$set": {
                "hashed_password": hashed_password,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"      ✓ Password updated successfully")
    else:
        print(f"      ✗ Failed to update password")
        client.close()
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("PASSWORD RESET COMPLETE")
    print("=" * 60)
    print(f"\nYou can now login with:")
    print(f"  Email:    {email}")
    print(f"  Password: {new_password}")
    print("\n" + "=" * 60 + "\n")
    
    client.close()
    return True


async def list_demo_users():
    """List all demo users in the database."""
    
    print("\n" + "=" * 60)
    print("AVAILABLE DEMO USERS")
    print("=" * 60)
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        users = await db.users.find({}).to_list(None)
        
        if not users:
            print("\nNo users found in database")
            return
        
        print(f"\nFound {len(users)} user(s):\n")
        
        for i, user in enumerate(users, 1):
            status = "✓ Verified" if user.get('is_verified') else "✗ Unverified"
            print(f"{i}. {user.get('email')}")
            print(f"   Name: {user.get('full_name')}")
            print(f"   Shop: {user.get('shop_name')}")
            print(f"   Status: {status}")
            print()
        
        print("=" * 60 + "\n")
    
    finally:
        client.close()


async def main():
    """Main entry point."""
    
    print("\n" + "=" * 60)
    print("RetailMind Demo Password Reset Tool")
    print("=" * 60)
    
    # Show available users
    await list_demo_users()
    
    # Get user input
    email = input("Enter email address to reset: ").strip()
    
    if not email:
        print("✗ Email is required")
        return
    
    print("\nPassword requirements:")
    print("  • Minimum 8 characters")
    print("  • Can contain letters, numbers, and symbols")
    
    password = input("\nEnter new password: ").strip()
    
    if len(password) < 8:
        print("\n✗ Password must be at least 8 characters")
        return
    
    password_confirm = input("Confirm password: ").strip()
    
    if password != password_confirm:
        print("\n✗ Passwords do not match")
        return
    
    # Reset password
    success = await reset_demo_password(email, password)
    
    if not success:
        print("\n✗ Password reset failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
