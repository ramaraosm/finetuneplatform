from sqlalchemy import Column, Integer, String, DateTime, Text, LargeBinary, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone


Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    dataset_filename = Column(String, index=True, nullable=True)
    base_model = Column(String)
    new_model_name = Column(String, unique=True, nullable=True)
    dataset_type = Column(String, nullable=True)
    status = Column(String, default="QUEUED")
    task_type = Column(String, default="finetuning")
    input_data = Column(JSON, nullable=True) # New column to store input for inference jobs
    result_data = Column(JSON, nullable=True) # New column for storing inference results (JSONB in Postgres)    
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Job(id='{self.id}', status='{self.status}', type='{self.task_type}')>"
