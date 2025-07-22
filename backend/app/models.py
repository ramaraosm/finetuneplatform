'''
from pydantic import BaseModel, Field
from typing import Optional, Literal

class JobCreate(BaseModel):
    base_model: Literal["unsloth/Phi-3-mini-4k-instruct-gguf", "unsloth/llama-3-8b-Instruct"]
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
    base_model: Literal["unsloth/Qwen2-7b-bnb-4bit", "unsloth/gemma-7b-bnb-4bit","unsloth/llama-3-8b-Instruct"]
    dataset_type: Literal["Q&A", "Conversational", "Reasoning"]
    new_model_name: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")

    # This is the new class method to handle form data
    @classmethod
    def as_form(
        cls,
        base_model: Literal["unsloth/Qwen2-7b-bnb-4bit", "unsloth/gemma-7b-bnb-4bit","unsloth/llama-3-8b-Instruct"] = Form(...),
        dataset_type: Literal["Q&A", "Conversational", "Reasoning"] = Form(...),
        new_model_name: str = Form(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$"),
    ) -> "JobCreate": # The -> "JobCreate" is for type hinting, ensures it returns an instance of JobCreate
        return cls(
            base_model=base_model,
            dataset_type=dataset_type,
            new_model_name=new_model_name
        )

class Job(BaseModel):
    id: str
    status: str
    base_model: str
    new_model_name: Optional[str] = None
    error_message: Optional[str] = None

class Config:
        from_attributes = True       

# Define a Pydantic model for the request body (input string)
class ChatInput(BaseModel):
    prompt: str
    modelId: str

# Define a Pydantic model for the response body (output string)
class ChatResponse(BaseModel):
    generated_text: str     

class InferenceRequestInput(BaseModel):
    job_id:str
    prompt: str
    huggingface_repo: str

class InferenceRequestResponse(BaseModel):
    job_id: str
    status: str # "accepted", "processing_inference", "completed_inference", "failed_inference"
    result: dict = None # To hold the inference output data        