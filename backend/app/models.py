'''
from pydantic import BaseModel, Field
from typing import Optional, Literal

class JobCreate(BaseModel):
    base_model: Literal["unsloth/Phi-3-mini-4k-instruct-gguf", "unsloth/llama-3-8b-Instruct-gguf"]
    dataset_type: Literal["Q&A", "Conversational", "Reasoning"]
    new_model_name: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")

class Job(BaseModel):
    id: int
    status: str
    base_model: str
    new_model_name: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
'''

from pydantic import BaseModel, Field
from typing import Optional, Literal
from fastapi import Form # <--- Import Form

class JobCreate(BaseModel):
    base_model: Literal["unsloth/Phi-3-mini-4k-instruct-gguf", "unsloth/llama-3-8b-Instruct-gguf"]
    dataset_type: Literal["Q&A", "Conversational", "Reasoning"]
    new_model_name: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")

    # This is the new class method to handle form data
    @classmethod
    def as_form(
        cls,
        base_model: Literal["unsloth/Phi-3-mini-4k-instruct-gguf", "unsloth/llama-3-8b-Instruct-gguf"] = Form(...),
        dataset_type: Literal["Q&A", "Conversational", "Reasoning"] = Form(...),
        new_model_name: str = Form(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$"),
    ) -> "JobCreate": # The -> "JobCreate" is for type hinting, ensures it returns an instance of JobCreate
        return cls(
            base_model=base_model,
            dataset_type=dataset_type,
            new_model_name=new_model_name
        )

class Job(BaseModel):
    id: int
    status: str
    base_model: str
    new_model_name: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True        