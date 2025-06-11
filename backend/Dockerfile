FROM python:3.10-slim

WORKDIR /app

# Set environment variables to prevent buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY shared /app/shared
COPY /backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY /backend/app /app/app


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]