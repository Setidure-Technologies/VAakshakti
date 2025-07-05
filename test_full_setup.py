#!/usr/bin/env python3

"""
Comprehensive test for the entire Celery setup
"""

import os
import time
import json
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all imports work correctly"""
    try:
        logger.info("Testing imports...")
        
        # Test Celery instance import
        from app.core.celery_instance import celery_app
        logger.info("✓ Celery instance imported successfully")
        
        # Test task imports
        from tasks.component_tasks import (
            transcribe_audio_task,
            extract_audio_features_task,
            create_final_summary_task
        )
        logger.info("✓ Component tasks imported successfully")
        
        from tasks.notification import (
            send_booking_reminder,
            cleanup_expired_bookings
        )
        logger.info("✓ Notification tasks imported successfully")
        
        from tasks.speech_evaluation import (
            evaluate_speech_background,
            analyze_language_background
        )
        logger.info("✓ Speech evaluation tasks imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Import test failed: {e}")
        return False

def test_celery_configuration():
    """Test Celery configuration"""
    try:
        logger.info("Testing Celery configuration...")
        
        from app.core.celery_instance import celery_app
        
        # Test broker URL
        broker_url = celery_app.conf.broker_url
        logger.info(f"Broker URL: {broker_url}")
        
        # Test backend URL
        backend_url = celery_app.conf.result_backend
        logger.info(f"Backend URL: {backend_url}")
        
        # Test task routing
        task_routes = celery_app.conf.task_routes
        logger.info(f"Task routes configured: {len(task_routes)} routes")
        
        # Test registered tasks
        registered_tasks = list(celery_app.tasks.keys())
        our_tasks = [t for t in registered_tasks if not t.startswith('celery.')]
        logger.info(f"✓ Found {len(our_tasks)} custom tasks registered")
        
        for task in our_tasks:
            logger.info(f"  - {task}")
            
        return True
        
    except Exception as e:
        logger.error(f"✗ Celery configuration test failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        logger.info("Testing Redis connection...")
        
        import redis
        from app.core.celery_instance import celery_app
        
        # Get Redis URL from Celery config
        redis_url = celery_app.conf.broker_url
        
        # Parse URL
        if redis_url.startswith("redis://"):
            parts = redis_url.replace("redis://", "").split("/")
            host_port = parts[0]
            db = int(parts[1]) if len(parts) > 1 else 0
            
            if ":" in host_port:
                host, port = host_port.split(":")
                port = int(port)
            else:
                host = host_port
                port = 6379
                
            r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            
            # Test connection
            r.ping()
            logger.info("✓ Redis connection successful")
            
            # Test basic operations
            r.set("test_key", "test_value")
            value = r.get("test_key")
            if value == "test_value":
                logger.info("✓ Redis read/write operations work")
                r.delete("test_key")
                return True
            else:
                logger.error("✗ Redis read/write operations failed")
                return False
                
    except Exception as e:
        logger.error(f"✗ Redis connection test failed: {e}")
        return False

def test_worker_availability():
    """Test if Celery workers are available"""
    try:
        logger.info("Testing worker availability...")
        
        from app.core.celery_instance import celery_app
        
        # Check active workers
        inspect = celery_app.control.inspect()
        
        # Get worker stats
        stats = inspect.stats()
        if stats:
            logger.info(f"✓ Found {len(stats)} active workers:")
            for worker_name, worker_stats in stats.items():
                logger.info(f"  - {worker_name}: {worker_stats.get('pool', {}).get('processes', 'N/A')} processes")
            
            # Check registered tasks on workers
            registered = inspect.registered()
            if registered:
                logger.info("✓ Workers have registered tasks")
                for worker_name, tasks in registered.items():
                    our_tasks = [t for t in tasks if not t.startswith('celery.')]
                    logger.info(f"  - {worker_name}: {len(our_tasks)} custom tasks")
                    
            return True
        else:
            logger.error("✗ No active workers found")
            return False
            
    except Exception as e:
        logger.error(f"✗ Worker availability test failed: {e}")
        return False

def test_task_dispatch():
    """Test task dispatching"""
    try:
        logger.info("Testing task dispatch...")
        
        from app.core.celery_instance import celery_app
        
        # Create a simple test task
        @celery_app.task(bind=True, name="test_dispatch_task")
        def test_dispatch_task(self, message="Hello from test"):
            return f"Task {self.request.id} received: {message}"
        
        # Dispatch the task
        result = test_dispatch_task.delay("Test message")
        logger.info(f"✓ Task dispatched with ID: {result.id}")
        
        # Try to get result with timeout
        try:
            task_result = result.get(timeout=10)
            logger.info(f"✓ Task completed: {task_result}")
            return True
        except Exception as e:
            logger.error(f"✗ Task dispatch failed or timed out: {e}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Task dispatch test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        logger.info("Testing database connection...")
        
        from database import sync_engine_sqlalchemy
        from sqlmodel import text
        
        # Test database connection
        with sync_engine_sqlalchemy.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("✓ Database connection successful")
                return True
            else:
                logger.error("✗ Database query failed")
                return False
                
    except Exception as e:
        logger.error(f"✗ Database connection test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=== Comprehensive Celery Setup Test ===")
    
    tests = [
        ("Imports", test_imports),
        ("Celery Configuration", test_celery_configuration),
        ("Redis Connection", test_redis_connection),
        ("Database Connection", test_database_connection),
        ("Worker Availability", test_worker_availability),
        ("Task Dispatch", test_task_dispatch),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        results[test_name] = test_func()
        
    # Summary
    logger.info("\n=== Test Summary ===")
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your Celery setup is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())