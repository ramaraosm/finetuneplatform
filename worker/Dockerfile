# We use the Unsloth image which has CUDA and other drivers pre-installed
FROM unsloth/unsloth:2024.5-py3.10-cuda12.1-runtime

WORKDIR /app

# Copy only requirements to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .
COPY shared /app/shared
# Command to run the worker script
CMD ["python", "worker.py"]