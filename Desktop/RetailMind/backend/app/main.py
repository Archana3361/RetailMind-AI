import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.services.ml_service import _load_ml

from app.routes import auth, products, categories, customers, suppliers
from app.routes import sales, purchases, inventory, dashboard, analytics, reports, ml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RetailMind AI backend...")
    await connect_to_mongo()
    _load_ml()  # Load model once at startup
    yield
    # Shutdown
    await close_mongo_connection()
    logger.info("RetailMind AI backend stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "RetailMind AI — AI-Powered Retail Management, "
        "Business Analytics & Demand Prediction Platform"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(customers.router)
app.include_router(suppliers.router)
app.include_router(sales.router)
app.include_router(purchases.router)
app.include_router(inventory.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(ml.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
