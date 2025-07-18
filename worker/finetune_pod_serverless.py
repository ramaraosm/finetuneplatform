import requests
import json
import os
import time
import base64
from dotenv import load_dotenv
from shared.utils import logger
import runpod

logger = logger.setup_logger('finetune_with_serverless_pod')

# Load environment variables from .env file
load_dotenv()

# --- RunPod Serverless API Configuration ---
# Your RunPod API Key from https://www.runpod.io/console/user/api-keys
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
if not RUNPOD_API_KEY:
    logger.error("RUNPOD_API_KEY environment variable not set. Please set it in your .env file.")
    exit(1)

# Your Serverless Endpoint ID from the RunPod Console (e.g., https://api.runpod.ai/v2/YOUR_ENDPOINT_ID)
RUNPOD_SERVERLESS_ENDPOINT_ID = os.getenv("RUNPOD_SERVERLESS_ENDPOINT_ID")
if not RUNPOD_SERVERLESS_ENDPOINT_ID:
    logger.error("RUNPOD_SERVERLESS_ENDPOINT_ID environment variable not set. Please set it.")
    exit(1)

def convert_sets_to_lists(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_sets_to_lists(elem) for elem in obj]
    else:
        return obj    

def run_finetuning_job_serverless(job):
    logger.info(f"Starting finetuning process via RunPod Serverless...")

    # --- Step 1: Upload the dataset to your RunPod Network Volume ---
    # This path is where the file will reside *on your Network Volume*
    S3_DATASET_KEY = f"datasets/{job.id}_{job.dataset_filename}"
    
    # --- Step 2: Define parameters for the Serverless fine-tuning job ---
    # These parameters will be sent as `job['input']` to your handler.py
    # `dataset_path` here is the path *relative to the Network Volume's mount point (/workspace)*
    # "hf_repo_id": f"{os.getenv('HUGGING_FACE_USERNAME')}/finetuned-{job.new_model_name}-{int(time.time())}",
    JOB_INPUT_PARAMETERS = {
        "base_model": 'unsloth/Qwen3-14B',
        "dataset_path": S3_DATASET_KEY, # Path on the Network Volume
        "output_dir": f"output", # Output path on Network Volume
        "epochs": 2,
        "batch_size": 4,
        "learning_rate": 2e-4,
        "gradient_accumulation_steps": 4,
        "hf_repo_id": f"{os.getenv('HUGGING_FACE_USERNAME')}/finetuned-{job.new_model_name}",
        "hf_private_repo": False,
        "hf_commit_message": "Fine-tuning job initiated by RunPod Serverless client.",
    }

    # --- Step 3: Call the RunPod Serverless Endpoint ---
    logger.info(f"Submitting Serverless job with parameters: {JOB_INPUT_PARAMETERS}")
    try:
        # run_sync is blocking and waits for completion
        # run_async is non-blocking and returns a job_id immediately
        # POST https://api.runpod.ai/v2/{endpoint_id}/runsync
        runpod.api_key = RUNPOD_API_KEY
        endpoint = runpod.Endpoint(RUNPOD_SERVERLESS_ENDPOINT_ID)

        job_response = endpoint.run_sync({"input": convert_sets_to_lists(JOB_INPUT_PARAMETERS)})
        '''
        job_response = endpoint.run_sync(
            runpod.endpoint_id,
            JOB_INPUT_PARAMETERS,
            timeout=3600 # Adjust timeout for fine-tuning, e.g., 1 hour (3600 seconds)
        )
        
        '''
        
        # If using run_async:
        # job_response = runpod.run(runpod.endpoint_id, JOB_INPUT_PARAMETERS)
        # print(f"Job submitted asynchronously with ID: {job_response['id']}")
        # Poll manually using runpod.get_job(job_response['id'])
        
        logger.info(f"\n--- Serverless Job Finished ---")
        logger.info(f"Job Status: {job_response.get('status')}")
        logger.info(f"Job Output: {job_response.get('output')}")
        if job_response.get('error'):
            logger.error(f"Job Error: {job_response.get('error')}")
        
        return job_response

    except Exception as e:
        logger.error(f"Error submitting or running Serverless job: {e}")
        return {"status": "ERROR", "error": str(e)}      
def run_finetuning_job(job):
    run_finetuning_job_serverless(job)

