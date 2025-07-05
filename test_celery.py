#!/usr/bin/env python3

"""
Test script to verify Celery setup
"""

import os
import sys
import time
import redis
import logging
from app.core.celery_instance import celery_app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        logger.info(f"Testing Redis connection to: {redis_url}")
        
        # Parse Redis URL
        if redis_url.startswith("redis://"):
            # Extract host and port
            parts = redis_url.replace("redis://", "").split("/")
            host_port = parts[0]
            db = int(parts[1]) if len(parts) > 1 else 0
            
            if ":" in host_port:
                host, port = host_port.split(":")
                port = int(port)
            else:
                host = host_port
                port = 6379
                
            r = redis.Redis(host=host, port=port, db=db)
            r.ping()
            logger.info("✓ Redis connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False

def test_celery_connection():
    """Test Celery broker connection"""
    try:
        # Check if Celery can connect to broker
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            logger.info("✓ Celery broker connection successful")
            logger.info(f"Active workers: {list(stats.keys())}")
            return True
        else:
            logger.warning("✗ No active Celery workers found")
            return False
    except Exception as e:
        logger.error(f"✗ Celery broker connection failed: {e}")
        return False

def test_task_registration():
    """Test task registration"""
    try:
        registered_tasks = list(celery_app.tasks.keys())
        logger.info(f"✓ Found {len(registered_tasks)} registered tasks:")
        for task in registered_tasks:
            if not task.startswith('celery.'):
                logger.info(f"  - {task}")
        return True
    except Exception as e:
        logger.error(f"✗ Task registration check failed: {e}")
        return False

def main():
    logger.info("=== Celery Setup Test ===")
    
    # Test Redis connection
    redis_ok = test_redis_connection()
    
    # Test Celery connection
    celery_ok = test_celery_connection()
    
    # Test task registration
    tasks_ok = test_task_registration()
    
    logger.info("\n=== Test Summary ===")
    logger.info(f"Redis Connection: {'✓' if redis_ok else '✗'}")
    logger.info(f"Celery Connection: {'✓' if celery_ok else '✗'}")
    logger.info(f"Task Registration: {'✓' if tasks_ok else '✗'}")
    
    if redis_ok and celery_ok and tasks_ok:
        logger.info("🎉 All tests passed! Celery setup looks good.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())