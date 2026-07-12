import logging
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.db.database import get_db, async_session_maker
from app.api.v1.router import api_router
from app.services.scoring import recalculate_all_departments

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# APScheduler daily recalculation job
# ---------------------------------------------------------------------------
# Why APScheduler over FastAPI BackgroundTasks?
#   - BackgroundTasks are request-scoped: they can only fire in response to an
#     HTTP request.  There is no built-in way to schedule a cron-like task.
#   - APScheduler provides a true cron trigger, survives across the entire
#     application lifetime, and supports async jobs natively via AsyncIOScheduler.
#   - The tradeoff is one extra dependency, but it's lightweight and battle-tested.
# ---------------------------------------------------------------------------

scheduler = AsyncIOScheduler()


async def _daily_score_recalculation():
    """
    Scheduled job that recalculates ESG scores for all active departments.
    Runs the trailing 30-day window ending today.
    """
    logger.info("⏰ Starting scheduled daily ESG score recalculation...")
    period_end = date.today()
    period_start = period_end - timedelta(days=30)

    async with async_session_maker() as db:
        try:
            await recalculate_all_departments(db, period_start, period_end)
            logger.info("✅ Daily ESG score recalculation completed successfully.")
        except Exception:
            logger.exception("❌ Daily ESG score recalculation failed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Starts APScheduler on startup and shuts it down cleanly on shutdown.
    """
    # Schedule the daily recalculation at 02:00 UTC
    scheduler.add_job(
        _daily_score_recalculation,
        trigger="cron",
        hour=2,
        minute=0,
        id="daily_esg_score_recalc",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "🗓️  APScheduler started — daily ESG recalculation scheduled at 02:00 UTC"
    )
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("🛑 APScheduler shut down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Verify DB connection
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"error: {str(e)}"
        }

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
