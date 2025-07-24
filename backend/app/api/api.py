import os
from dotenv import load_dotenv
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .. import models
from ..db.session import SessionLocal
from shared.utils import logger
from shared.utils.celery_app import celery_app
from shared.db import base
import uuid

#from celery_worker.worker import run_runpod_inference_task # <--- Import the specific task

logger = logger.setup_logger('backend')

load_dotenv()

api_router = APIRouter()

# Dependency to get DB session
def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


'''
@api_router.post("/jobs", response_model=models.Job, status_code=201)
def create_job(
    job_in: models.JobCreate = Depends(),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    logger.info('Inside create Job ')
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    # Save the uploaded file
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    logger.info('job saving to db')
    job = base.Job(
        dataset_filename=file.filename,
        base_model=job_in.base_model,
        new_model_name=job_in.new_model_name,
        dataset_type=job_in.dataset_type,
        status="QUEUED"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
'''

@api_router.post("/jobs", response_model=models.Job, status_code=201)
def create_job(
    # CHANGE THIS LINE:
    job_in: models.JobCreate = Depends(models.JobCreate.as_form), # <--- Here's the change!
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Your existing logic remains the same, as job_in will now be correctly populated
    # ...
    logger.info('Inside create Job ')
    if not file.filename.endswith('.jsonl'):
        raise HTTPException(status_code=400, detail="Only JSONL files are allowed.")

    # Save the uploaded file
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    logger.info('job saving to db')
    job = base.Job(
        id=str(uuid.uuid4()),
        dataset_filename=file.filename,
        base_model=job_in.base_model,
        new_model_name=job_in.new_model_name,
        dataset_type=job_in.dataset_type,
        status="QUEUED"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@api_router.get("/jobs/{job_id}", response_model=models.Job)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(base.Job).filter(base.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.post(
    "/inference/generate_text", # New endpoint for inference
    response_model=models.InferenceRequestResponse,
    status_code=202, # 202 Accepted for async processing
    summary="Submit text for asynchronous inference via RunPod"
)
def submit_inference_request(input_data: models.InferenceRequestInput):
    request_id = str(uuid.uuid4())
    print(f'request_id for inference: {request_id}')
    print(f'input_data submitted for inference: {input_data}')
    db = SessionLocal()
    try:
        # Create an entry in your database to track this inference request
        # You might need to add a 'task_type' column to your Job model
        # or create a new 'InferenceRequest' model if Job is strictly for finetuning.
        new_job = base.Job(
            id=request_id,
            status="ACCEPTED",
            task_type="inference", # New field
            input_data={"text": input_data.prompt}, # Store input for tracking
            base_model=input_data.huggingface_repo, # Example
            # Other fields as necessary
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job) # Refresh to get auto-generated fields like created_at

        # Delegate the actual inference task to the Celery worker
        # This is the "call a method exposed from worker" part
        logger.info('Before calling run_runpod_inference_task')
        print("[INFO] Celery broker URL:", celery_app.conf.broker_url)
        task = celery_app.send_task("run_runpod_inference_task", args=[request_id,input_data.prompt, input_data.huggingface_repo])
        #run_runpod_inference_task.delay(input_data.job_id,input_data.prompt, input_data.huggingface_repo) # .delay() sends to message queue
        return models.InferenceRequestResponse(job_id=request_id, status="accepted")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit inference request: {e}")
    finally:
        db.close()


@api_router.get(
    "/inference/{request_id}",
    response_model=models.InferenceRequestResponse,
    summary="Get status and result of an inference request"
)
def get_inference_result(request_id: str, db: Session = Depends(get_db)):
    db = SessionLocal()
    try:
        job = db.query(base.Job).filter(base.Job.id == request_id).first()
        #job = db.query(models.Job).filter(models.Job.id == request_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Inference request not found.")

        return models.InferenceRequestResponse(
            job_id=job.id,
            status=job.status,
            result=job.result_data, # Assuming result_data column exists and stores the dict
            error_message=job.error_message if job.error_message is not None else ""
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit inference status request: {e}")
    finally:
        db.close()