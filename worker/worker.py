import time
import os
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import sys
from shared.utils import logger
logger = logger.setup_logger('worker')

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path to import from backend
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.db.base import Job

DATABASE_URL = os.getenv("DATABASE_URL")
WORKER_MODE = os.getenv("WORKER_MODE", "GPU") # Default to GPU mode

# Dynamically import the correct module
if WORKER_MODE == "GPU":
    import finetune_with_custom_pod
elif WORKER_MODE == "CPU_MOCK":
    import finetune_mock
else:
    raise ValueError("Invalid WORKER_MODE. Choose 'GPU' or 'CPU_MOCK'.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_job_status(db, job_id, status, error_message=None):
    stmt = (
        update(Job)
        .where(Job.id == job_id)
        .values(status=status, error_message=error_message)
    )
    db.execute(stmt)
    db.commit()
    print(f"Updated job {job_id} to status {status}")

def poll_for_jobs():
    logger.info('In poll for jobs')
    print(f"Worker started in {WORKER_MODE} mode. Polling for jobs...")
    while True:
        db = SessionLocal()
        try:
            job_to_process = db.query(Job).filter(Job.status == "QUEUED").order_by(Job.created_at).first()

            if job_to_process:
                print(f"Found job: {job_to_process.id}")
                update_job_status(db, job_to_process.id, "RUNNING")

                try:
                    # Execute the correct logic based on the mode
                    if WORKER_MODE == "GPU":
                        finetune_with_custom_pod.run_finetuning_job(job_to_process)
                    elif WORKER_MODE == "CPU_MOCK":
                        finetune_mock.run_mock_finetuning_job(job_to_process)
                    
                    update_job_status(db, job_to_process.id, "COMPLETED")

                except Exception as e:
                    print(f"Error processing job {job_to_process.id}: {e}")
                    import traceback
                    traceback.print_exc()
                    update_job_status(db, job_to_process.id, "FAILED", error_message=str(e))
            else:
                time.sleep(10)
        finally:
            db.close()

if __name__ == "__main__":
    poll_for_jobs()