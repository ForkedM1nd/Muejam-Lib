"""Celery tasks for discovery system."""
from celery import shared_task
from .trending import TrendingCalculator
from .personalization import PersonalizationEngine
from prisma import Prisma
import asyncio
import threading


def _run_async(coro):
    """Run async code from sync context, even inside active event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    try:
        import nest_asyncio

        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    except Exception:
        pass

    result = {}
    error = {}

    def _runner():
        try:
            result['value'] = asyncio.run(coro)
        except Exception as exc:
            error['value'] = exc

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()

    if 'value' in error:
        raise error['value']

    return result.get('value')


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
    _run_async(calculator.update_all_trending_scores())


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
    async def _apply_decay_async():
        db = Prisma()
        await db.connect()
        try:
            await db.execute_raw('UPDATE "UserInterest" SET score = score * 0.98')
        finally:
            await db.disconnect()

    _run_async(_apply_decay_async())
