import os
from celery import Celery

# Get Redis URL from environment variable
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Define the Celery application instance here
celery_app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "tasks.speech_evaluation",
        "tasks.notification",
        "tasks.component_tasks"
    ]
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

# Optional: If you have tasks in other modules, you can add them here
# celery_app.autodiscover_tasks(['tasks'])