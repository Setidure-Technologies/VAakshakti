#!/usr/bin/env python3

"""
Test script to dispatch a simple task and verify it's received
"""

import os
import time
import logging
from app.core.celery_instance import celery_app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="test_task")
def test_task(self, message="Hello World"):
    """Simple test task"""
    logger.info(f"Test task received: {message}")
    return f"Task completed with message: {message}"

def main():
    logger.info("=== Task Dispatch Test ===")
    
    try:
        # Dispatch test task
        logger.info("Dispatching test task...")
        result = test_task.delay("Test message from dispatcher")
        
        logger.info(f"Task dispatched with ID: {result.id}")
        
        # Wait for result (with timeout)
        try:
            task_result = result.get(timeout=10)
            logger.info(f"✓ Task completed: {task_result}")
            return 0
        except Exception as e:
            logger.error(f"✗ Task failed or timed out: {e}")
            return 1
            
    except Exception as e:
        logger.error(f"✗ Failed to dispatch task: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())