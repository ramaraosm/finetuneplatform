import requests
import json
import os
import uuid # For generating a unique job_id
import time # For polling in asynchronous calls

# --- Configuration ---
# Set these environment variables or replace with your actual values
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "YOUR_RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "YOUR_RUNPOD_ENDPOINT_ID")

# The base URL for RunPod Serverless API
RUNPOD_API_BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"

# Headers for authentication and content type
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {RUNPOD_API_KEY}"
}

def call_runpod_sync(prompt: str, huggingface_repo: str = None, job_id: str = None):
    """
    Calls the RunPod Serverless endpoint synchronously using /runsync.
    This is best for quick inferences (under ~30 seconds) where you want an immediate result.
    """
    if not RUNPOD_API_KEY or RUNPOD_API_KEY == "YOUR_RUNPOD_API_KEY":
        print("Error: RUNPOD_API_KEY not set or is default. Please configure it.")
        return None
    if not RUNPOD_ENDPOINT_ID or RUNPOD_ENDPOINT_ID == "YOUR_RUNPOD_ENDPOINT_ID":
        print("Error: RUNPOD_ENDPOINT_ID not set or is default. Please configure it.")
        return None

    job_id = job_id if job_id else str(uuid.uuid4())
    url = f"{RUNPOD_API_BASE_URL}/runsync"

    payload = {
        "input": {
            "job_id": job_id,
            "prompt": prompt
        }
    }
    if huggingface_repo:
        payload["input"]["huggingface_repo"] = huggingface_repo

    print(f"\n--- Calling /runsync for Job ID: {job_id} ---")
    print(f"Sending payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=300) # Increased timeout
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()
        print(f"--- Received Sync Response for Job ID: {job_id} ---")
        print(json.dumps(result, indent=2))
        return result

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP Error: {e.response.status_code} - {e.response.text}", "job_id": job_id}
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        return {"error": f"Connection Error: {e}", "job_id": job_id}
    except requests.exceptions.Timeout:
        print(f"Timeout Error: Request timed out after 90 seconds.")
        return {"error": "Request timed out", "job_id": job_id}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": f"Unexpected error: {e}", "job_id": job_id}

def call_runpod_async(prompt: str, huggingface_repo: str = None, custom_job_id: str = None, timeout_seconds: int = 300, poll_interval: int = 5):
    """
    Calls the RunPod Serverless endpoint asynchronously using /run and polls for results.
    This is ideal for longer-running inferences where you don't want to block your client.
    """
    if not RUNPOD_API_KEY or RUNPOD_API_KEY == "YOUR_RUNPOD_API_KEY":
        print("Error: RUNPOD_API_KEY not set or is default. Please configure it.")
        return None
    if not RUNPOD_ENDPOINT_ID or RUNPOD_ENDPOINT_ID == "YOUR_RUNPOD_ENDPOINT_ID":
        print("Error: RUNPOD_ENDPOINT_ID not set or is default. Please configure it.")
        return None

    job_id = custom_job_id if custom_job_id else str(uuid.uuid4())
    run_url = f"{RUNPOD_API_BASE_URL}/run"
    status_url_base = f"{RUNPOD_API_BASE_URL}/status"

    payload = {
        "input": {
            "job_id": job_id,
            "prompt": prompt
        }
    }
    if huggingface_repo:
        payload["input"]["huggingface_repo"] = huggingface_repo

    print(f"\n--- Submitting Async Job ID: {job_id} ---")
    print(f"Sending payload: {json.dumps(payload, indent=2)}")

    try:
        # Step 1: Submit the job
        response = requests.post(run_url, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        initial_response = response.json()
        runpod_job_id = initial_response.get('id')
        status = initial_response.get('status')

        if not runpod_job_id:
            raise ValueError(f"RunPod did not return a job ID: {initial_response}")

        print(f"RunPod Job submitted. RunPod Job ID: {runpod_job_id}. Initial status: {status}")

        # Step 2: Poll for job status
        start_time = time.time()
        status_url = f"{status_url_base}/{runpod_job_id}"

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"Job {runpod_job_id} timed out after {timeout_seconds} seconds.")

            print(f"[{time.strftime('%H:%M:%S', time.localtime())}] Polling status for RunPod Job ID: {runpod_job_id} (Elapsed: {elapsed_time:.0f}s)...")
            status_response = requests.get(status_url, headers=HEADERS)
            status_response.raise_for_status()
            status_data = status_response.json()
            current_status = status_data.get('status')

            if current_status == "COMPLETED":
                output_data = status_data.get('output')
                if output_data:
                    output_data['job_id'] = job_id # Add our original job_id for consistency
                    print(f"--- RunPod Async Job {runpod_job_id} COMPLETED ---")
                    print(json.dumps(output_data, indent=2))
                    return output_data
                else:
                    raise ValueError(f"RunPod job completed but no output found: {status_data}")
            elif current_status in ["FAILED", "CANCELED", "EXPIRED"]:
                error_message = status_data.get('error', 'No specific error message provided by RunPod.')
                print(f"--- RunPod Async Job {runpod_job_id} {current_status} ---")
                print(json.dumps(status_data, indent=2))
                return {
                    "inference_output": None,
                    "job_id": job_id,
                    "status": current_status.lower(),
                    "error_message": f"RunPod job {current_status}. Details: {error_message}"
                }
            
            time.sleep(poll_interval) # Wait before polling again

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP Error: {e.response.status_code} - {e.response.text}", "job_id": job_id}
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        return {"error": f"Connection Error: {e}", "job_id": job_id}
    except requests.exceptions.Timeout:
        print(f"Timeout Error: Polling timed out after {timeout_seconds} seconds.")
        return {"error": f"Polling timed out after {timeout_seconds} seconds.", "job_id": job_id}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": f"Unexpected error: {e}", "job_id": job_id}


if __name__ == "__main__":
    # --- Example Usage ---

    # Make sure to set your environment variables:
    # export RUNPOD_API_KEY="YOUR_API_KEY_HERE"
    # export RUNPOD_ENDPOINT_ID="YOUR_ENDPOINT_ID_HERE"

    # --- Synchronous Call Example ---
    print("--- Testing Synchronous Call ---")
    sync_prompt = "What is the primary function of a CPU?"
    sync_hf_repo = "distilbert-base-uncased-finetuned-sst-2-english" # This won't override as handler.py doesn't support it
    
    sync_result = call_runpod_sync(
        prompt=sync_prompt,
        huggingface_repo=sync_hf_repo,
        custom_job_id="my_sync_job_001"
    )
    if sync_result:
        print(f"\nSynchronous Inference Result for Job ID {sync_result.get('job_id')}:")
        print(f"Status: {sync_result.get('status')}")
        print(f"Output: {sync_result.get('inference_output')}")
        if sync_result.get('error_message'):
            print(f"Error: {sync_result.get('error_message')}")
    else:
        print("\nSynchronous call failed or returned no result.")

    print("\n" + "="*50 + "\n")

    # --- Asynchronous Call Example ---
    print("--- Testing Asynchronous Call (Polling) ---")
    async_prompt = "Explain the concept of quantum entanglement in simple terms."
    async_hf_repo = "distilbert-base-uncased-finetuned-sst-2-english" # This won't override
    
    async_result = call_runpod_async(
        prompt=async_prompt,
        huggingface_repo=async_hf_repo,
        custom_job_id="my_async_job_002",
        timeout_seconds=300, # Max 5 minutes for this job
        poll_interval=10     # Check status every 10 seconds
    )

    if async_result:
        print(f"\nAsynchronous Inference Result for Job ID {async_result.get('job_id')}:")
        print(f"Status: {async_result.get('status')}")
        print(f"Output: {async_result.get('inference_output')}")
        if async_result.get('error_message'):
            print(f"Error: {async_result.get('error_message')}")
    else:
        print("\nAsynchronous call failed or returned no result.")