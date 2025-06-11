from sqlalchemy import Column, Integer, String, DateTime, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    dataset_filename = Column(String, index=True)
    base_model = Column(String)
    new_model_name = Column(String, unique=True)
    dataset_type = Column(String)
    status = Column(String, default="QUEUED")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)