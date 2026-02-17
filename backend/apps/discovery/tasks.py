"""Celery tasks for discovery system."""
from celery import shared_task
from .trending import TrendingCalculator
from .personalization import PersonalizationEngine
from prisma import Prisma
import asyncio


@shared_task
def update_trending_scores():
    """
    Recompute trending scores for all stories.
    
    This task runs every 10-30 minutes to update trending scores
    based on recent engagement metrics.
    
    Requirements:
        - 16.3: Recompute trending scores as background job
        - 19.2: Run every 10-30 minutes
    """
    calculator = TrendingCalculator()
    asyncio.run(calculator.update_all_trending_scores())


@shared_task
def apply_daily_decay():
    """
    Apply daily decay to all interest scores.
    
    This task runs every 24 hours to decay user interest scores
    by multiplying them by 0.98.
    
    Requirements:
        - 10.6: Apply daily score decay of 0.98
        - 19.4: Run every 24 hours
    """
    async def run_decay():
        db = Prisma()
        await db.connect()
        try:
            # Multiply all interest scores by decay factor
            await db.execute_raw(
                "UPDATE \"UserInterest\" SET score = score * 0.98"
            )
        finally:
            await db.disconnect()
    
    asyncio.run(run_decay())
