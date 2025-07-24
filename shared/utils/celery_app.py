# celery_worker/celery_app.py
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv() # Load environment variables

REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")

print('REDIS_BROKER_URL in celery :',REDIS_BROKER_URL)

# Initialize the Celery app instance
celery_app = Celery('finetuneit_celery_app', broker=REDIS_BROKER_URL, backend=REDIS_BROKER_URL)

# Configure Celery for JSON serialization
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    imports=('celery_worker.worker',),
    # Optional: If you have many tasks, you might want to specify a task route
    # task_routes = {
    #     'celery_worker.worker.run_runpod_inference_task': {'queue': 'inference_queue'},
    #     # Add other task routes here
    # }
)

# You can also add autodiscover_tasks if you have tasks in multiple files
# celery_app.autodiscover_tasks(['celery_worker']) # Tells Celery to find tasks in this package

'''
celery_app.conf.task_routes = {
    "run_runpod_inference_task": {"queue": "default"},
}
'''