# We use the Unsloth image which has CUDA and other drivers pre-installed
# FROM unsloth/unsloth:2024.5-py3.10-cuda12.1-runtime
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY shared /app/shared
COPY /worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY celery_worker /app/celery_worker
# CMD ["python", "worker.py"]
# Set environment variables (optional, can be passed via docker-compose)
# ENV REDIS_BROKER_URL="redis://redis:6379/0"

# Command is now defined in docker-compose.yml
CMD ["celery", "-A", "celery_worker.celery_app", "worker", "--loglevel=info"]