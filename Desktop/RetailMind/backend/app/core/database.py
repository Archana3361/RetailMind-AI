from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        # Verify connection
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
        await create_indexes()
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise


async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    """Create necessary indexes for performance and uniqueness."""
    try:
        # Users
        await db.users.create_index("email", unique=True)
        await db.users.create_index("mobile")

        # OTP verifications
        await db.otp_verifications.create_index("email")
        await db.otp_verifications.create_index(
            "expires_at", expireAfterSeconds=0
        )

        # Products
        await db.products.create_index([("user_id", ASCENDING), ("sku", ASCENDING)], unique=True)
        await db.products.create_index([("user_id", ASCENDING), ("name", ASCENDING)])

        # Categories
        await db.categories.create_index([("user_id", ASCENDING), ("name", ASCENDING)], unique=True)

        # Customers
        await db.customers.create_index([("user_id", ASCENDING), ("email", ASCENDING)])
        await db.customers.create_index([("user_id", ASCENDING), ("phone", ASCENDING)])

        # Suppliers
        await db.suppliers.create_index([("user_id", ASCENDING), ("name", ASCENDING)])

        # Sales
        await db.sales.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        # Purchases
        await db.purchases.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        # Inventory transactions
        await db.inventory_transactions.create_index([("user_id", ASCENDING), ("product_id", ASCENDING)])
        await db.inventory_transactions.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        # Predictions
        await db.predictions.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


def get_database():
    return db
