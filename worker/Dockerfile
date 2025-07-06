# We use the Unsloth image which has CUDA and other drivers pre-installed
# FROM unsloth/unsloth:2024.5-py3.10-cuda12.1-runtime
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY shared /app/shared
COPY /worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY /worker /app
CMD ["python", "worker.py"]