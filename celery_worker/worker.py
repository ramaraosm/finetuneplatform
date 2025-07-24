import os
import time
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from celery import Celery
import json # New import for Redis communication
from .inference_client import call_runpod_sync, call_runpod_async # Assuming these are the functions you want to use
from shared.utils.celery_app import celery_app

from shared.utils import logger
logger = logger.setup_logger('celery-worker')

# Load environment variables
load_dotenv()

#celery_app.autodiscover_tasks(['celery_worker.worker']) # Tells Celery to find tasks in this package
print("[INFO] Celery broker URL:", celery_app.conf.broker_url)
# Add the parent directory to the path to import from backend
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.db.base import Job # Assuming Job model is in shared.db.base

DATABASE_URL = os.getenv("DATABASE_URL")
WORKER_MODE = "GPU-SERVERLESS" #os.getenv("WORKER_MODE", "GPU")

# --- End Celery App Setup ---

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_job_status(db, job_id, status, error_message=None, result_data=None):
    stmt = (
        update(Job)
        .where(Job.id == job_id)
        .values(status=status, error_message=error_message, result_data=result_data) # Add result_data if your Job model supports it
    )
    db.execute(stmt)
    db.commit()
    print(f"Updated job {job_id} to status {status}")

# --- Celery Task for Inference ---
# This method will be called by the backend service
@celery_app.task(bind=True, name='run_runpod_inference_task') # bind=True allows access to task instance (self)
def run_runpod_inference_task(self, job_id: str, prompt: str, huggingface_repo:str):
    """
    Celery task to delegate an inference job to RunPod.
    """
    db = SessionLocal()
    try:
        logger.info(f"Worker received inference task for request_id: {job_id}")
        
        # You need to create a Job entry in your DB for this inference request
        # or use a different model to track inference requests if Job is only for finetuning.
        # For simplicity, let's assume Job can track inference too, or you create a new InferenceRequest model.
        
        # If no Job object exists for this request_id (e.g., if it's a new inference type)
        # you might need to create one or update a separate inference table.
        # For now, let's assume you'll update status based on request_id in some store
        # or that a Job was created for this purpose by the backend.

        # Example: Update a dummy status in a Redis store or create/update an InferenceRequest DB table
        # Let's use the Job table for this example, creating a dummy Job if it doesn't exist.
        # In a real app, backend creates the Job/InferenceRequest, and worker updates it.
        
        # Find the job by request_id (assuming request_id is stored in job.id or a new column)
        job_to_process = db.query(Job).filter(Job.id == job_id).first()
        if not job_to_process:
            logger.error(f"Inference Job with ID {job_id} not found in DB.")
            # Create a dummy job or handle error
            # For simplicity, let's create one if not found. In production, backend should create it.
            new_job = Job(id=job_id, status="ACCEPTED", task_type="inference", base_model="ramaraohface/llama-finetuned38", dataset_path="n/a")
            db.add(new_job)
            db.commit()
            job_to_process = new_job
            logger.info(f"Created new dummy Job for inference: {job_id}")


        update_job_status(db, job_to_process.id, "PROCESSING_INFERENCE")

        # --- CALL YOUR RUNPOD INFERENCE LOGIC HERE ---
        logger.info(f"Calling RunPod inference for {job_id} with text: {prompt} and huggingface repo {huggingface_repo}...")
        
        # The `runpod_inference` module should contain a function like `run_inference`
        # that handles communication with RunPod and returns the inference result.
        inference_result = call_runpod_sync(job_id,prompt,huggingface_repo)

        inference_output_text = inference_result.get('output', {}).get('inference_output')

        logger.info(f"RunPod inference for {job_id} completed. Result: {inference_result}")
        logger.info(f"RunPod inference for {job_id} inference_output_text extracted. Result: {inference_output_text}")
        update_job_status(db, job_to_process.id, "COMPLETED_INFERENCE",result_data=inference_output_text)

    except Exception as e:
        logger.error(f"Error during RunPod inference for {job_id}: {e}", exc_info=True)
        update_job_status(db, job_id, "FAILED_INFERENCE", error_message=str(e))
    finally:
        db.close()


if __name__ == "__main__":
    # You can run both polling and Celery worker, but it's often better
    # to separate concerns and have different worker instances for different task types.
    # For a simple setup, you might run only one or the other based on environment variable.

    # To run Celery worker: celery -A worker.worker_main worker --loglevel=info
    # To run finetuning poller: python worker.py

    # For demonstration, let's assume this `worker.py` will primarily run the Celery worker
    # and the finetuning poller might be in a separate script or managed differently.
    # To start the Celery worker, you would typically run:
    # `celery -A worker.app.worker_main worker --loglevel=info` (adjust path)
    # The `poll_for_finetuning_jobs()` would be called if this script is directly executed
    # and you don't run the celery worker command.

    # If you want this single worker process to handle both, you'd need
    # to manage concurrent execution (e.g., using threading or asyncio loops).
    # For clarity, it's often better to have separate Docker containers/deployments
    # for `finetuning-worker` and `inference-worker`.

    # For now, let's make it clear this file contains the Celery task.
    # The actual execution of `celery_app.worker_main()` or `poll_for_finetuning_jobs()`
    # depends on how you run your Docker container's command.

    # Example: if you want to test the finetuning poller directly
    # poll_for_finetuning_jobs()
    pass # Celery worker is usually started via `celery -A ...` command