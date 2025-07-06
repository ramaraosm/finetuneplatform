import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from .. import models
from ..db.session import SessionLocal
from shared.utils import logger
from shared.db import base


logger = logger.setup_logger('backend')

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
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(base.Job).filter(base.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job