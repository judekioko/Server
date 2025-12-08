# bursary/background_tasks.py
"""
Background task management for production
"""

import logging
from concurrent.futures import ThreadPoolExecutor
import atexit

logger = logging.getLogger(__name__)

# Global thread pool for background tasks
executor = None

def initialize():
    """Initialize background task system"""
    global executor
    if executor is None:
        executor = ThreadPoolExecutor(
            max_workers=3,
            thread_name_prefix="bursary_bg"
        )
        logger.info("✅ Background task executor initialized")
    
    # Register cleanup
    atexit.register(shutdown)

def submit_task(func, *args, **kwargs):
    """Submit a task to background executor"""
    global executor
    if executor is None:
        initialize()
    
    return executor.submit(func, *args, **kwargs)

def shutdown():
    """Clean shutdown of background tasks"""
    global executor
    if executor:
        logger.info("🔄 Shutting down background task executor...")
        executor.shutdown(wait=False)
        executor = None