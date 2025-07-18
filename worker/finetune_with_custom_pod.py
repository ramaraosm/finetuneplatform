import requests
import json
import os
import time
import base64
from dotenv import load_dotenv
from shared.utils import logger

logger = logger.setup_logger('finetune_with custom_pod')

# Load environment variables from .env file
load_dotenv()

POD_IP = os.getenv("RUNPOD_IP")
HFACE_USERNAME = os.getenv("HUGGING_FACE_USERNAME")
SERVER_URL = f"{POD_IP}"
EXECUTE_ENDPOINT = f"{SERVER_URL}/execute_script"
STATUS_ENDPOINT = f"{SERVER_URL}/job_status"

output_dir="/workspace/output"

# --- Functions to interact with the executor server ---
def send_script_to_pod(job, script_content, script_params):
    payload = {
        "script_content": script_content,
        "script_params": script_params
    }
    logger.info(f"Sending script to {EXECUTE_ENDPOINT}...")
    try:
        response = requests.post(EXECUTE_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.info(f"Error sending script: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.info(f"Server response: {e.response.text}")
        return None

def poll_job_status(job_id):
        try:
            response = requests.get(f"{STATUS_ENDPOINT}/{job_id}", timeout=10)
            response.raise_for_status()
            status_data = response.json()
            
            status = status_data.get("status")
            output = status_data.get("output", "").strip()
            error = status_data.get("error", "").strip()

            logger.info(f"\nJob {job_id} Status: {status}")
            
            if output:
                logger.info(f"--- Script Output (partial) ---\n{output[-1000:]}\n--- End Output ---") # Show last 1000 chars

            if status in ["COMPLETED", "FAILED", "ERROR"]:
                logger.info(f"\n--- Final Job Details for {job_id} ---")
                logger.info(f"Final Status: {status}")
                if output:
                    logger.info(f"Full Output:\n{output}")
                if error:
                    logger.info(f"Error Details:\n{error}")
                return status_data
            
            time.sleep(15) # Poll every 15 seconds

        except requests.exceptions.RequestException as e:
            print(f"Error polling job status for {job_id}: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during polling: {e}")
            return None

def run_finetuning_job(job):
    print(f"Starting finetuning for job {job.id}...")

        # --- Fine-tuning Script to send ---
    # This reads the content of the finetune_template.py
    DATA_SCRIPT_PATH = "prepare_data.py"
    FINE_TUNE_SCRIPT_PATH = "finetune_template.py"
    DATASET_PATH = f"/app/uploads/{job.dataset_filename}"

    if not os.path.exists(DATASET_PATH):
        print(f"Error: Fine-tune script '{DATASET_PATH}' not found.")
        exit(1)

    with open(DATA_SCRIPT_PATH, "r") as f:
        data_script_content = f.read()    

    with open(DATASET_PATH, "rb") as f:
            dataset_content = base64.b64encode(f.read()).decode() 

    #dataset_script_content = f"echo '{dataset_content}' | base64 -d > /workspace/dataset.jsonl"     

    DATA_JOB_PARAMETERS = {
            "base64_dataset_content": dataset_content
        }

    if not os.path.exists(FINE_TUNE_SCRIPT_PATH):
        print(f"Error: Fine-tune script '{FINE_TUNE_SCRIPT_PATH}' not found.")
        exit(1)

    with open(FINE_TUNE_SCRIPT_PATH, "r") as f:
        finetune_script_content = f.read()

    # --- Parameters for the fine-tuning job ---
    # These will be passed to your finetune_template.py via the params_file
    JOB_PARAMETERS = {
        "base_model": f"{job.base_model}",
        "dataset_path": "/workspace/dataset.jsonl", # This must exist on the Pod's volume
        "output_dir": "/workspace/output",
        "epochs": 2,
        "batch_size": 4,
        "learning_rate": 2e-4,
        "gradient_accumulation_steps": 4,
        "hf_repo_id": f"{HFACE_USERNAME}/Finetuned-{job.new_model_name}", # !!! IMPORTANT: CHANGE THIS !!!
        "hf_private_repo": False, # Set to True for a private repo
        "hf_commit_message": "Fine-tuning complete on RunPod with custom data",
    }

    # Ensure Pod IP and Port are correctly configured
    if POD_IP is None:
        print("Please configure your RunPod Pod IP and Mapped HTTP Port in client_script.py.")
        exit(1)

    print(f"Connecting to Pod at {SERVER_URL}")

    # Step 1: Send the fine-tuning script and parameters
    submit_response = send_script_to_pod(job, data_script_content, DATA_JOB_PARAMETERS)

    if submit_response and submit_response.get("job_id"):
        job_id = submit_response["job_id"]
        print(f"Successfully submitted job {job_id}. Status: {submit_response.get('status')}")

        # Step 2: Poll for job status
        final_status_data = poll_job_status(job_id)

        if final_status_data:
            logger.info(f"\nJob {job_id} finished with final status: {final_status_data.get('status')}")
            # You can add logic here to trigger further actions based on status
        else:
            logger.info(f"Could not retrieve final status for job {job_id}.")
    else:
        logger.info("Failed to submit job or retrieve job ID.")
        
     # Step 1: Send the fine-tuning script and parameters
    logger.info(f"job parameters : {JOB_PARAMETERS}")
    submit_response = send_script_to_pod(job, finetune_script_content, JOB_PARAMETERS)

    if submit_response and submit_response.get("job_id"):
        job_id = submit_response["job_id"]
        logger.info(f"Successfully submitted job {job_id}. Status: {submit_response.get('status')}")

        # Step 2: Poll for job status
        final_status_data = poll_job_status(job_id)

        if final_status_data:
            logger.info(f"\nJob {job_id} finished with final status: {final_status_data.get('status')}")
            # You can add logic here to trigger further actions based on status
        else:
            logger.info(f"Could not retrieve final status for job {job_id}.")
    else:
        logger.info("Failed to submit job or retrieve job ID.")    
        