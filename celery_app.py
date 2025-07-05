"""
Celery configuration for background task processing
"""

import os
from app.core.celery_instance import celery_app
from celery.signals import worker_ready
import logging
import tasks.component_tasks
import tasks.notification
import tasks.speech_evaluation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Task routing
celery_app.conf.task_routes = {
    "tasks.notification.*": {"queue": "notifications"},
    "tasks.component_tasks.transcribe_audio_task": {"queue": "transcription"},
    "tasks.component_tasks.audio_features_task": {"queue": "audio_processing"},
    "tasks.component_tasks.emotion_text_task": {"queue": "text_analysis"},
    "tasks.component_tasks.sentiment_text_task": {"queue": "text_analysis"},
    "tasks.component_tasks.linguistic_text_task": {"queue": "text_analysis"},
    "tasks.component_tasks.grammar_task": {"queue": "llm_feedback"},
    "tasks.component_tasks.content_comparison_task": {"queue": "llm_feedback"},
    "tasks.component_tasks.pronunciation_task": {"queue": "llm_feedback"},
    "tasks.component_tasks.create_final_summary_task": {"queue": "llm_feedback"},
}

from celery.signals import task_prerun, task_postrun, task_failure

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Called when worker is ready"""
    logger.info(f"Celery worker is ready. Sender: {sender.hostname}")

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Called before a task is executed"""
    logger.info(f"Task {task.name} [{task_id}] is about to be executed.")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, state=None, **kwargs):
    """Called after a task has been executed"""
    logger.info(f"Task {task.name} [{task_id}] finished with state {state} and result {retval}.")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """Called when a task fails"""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}", exc_info=True)

if __name__ == "__main__":
    celery_app.start()