import os
import requests
import json
import time
import base64
from shared.utils import logger
from dotenv import load_dotenv

logger = logger.setup_logger('worker')

# Load environment variables from .env file
load_dotenv()

# wget https://yourdomain.com/datasets/user123.csv -O /workspace/data.csv && \
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
#RUNPOD_ENDPOINT = "https://api.runpod.ai/v2/graphql"
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID") # Replace with your actual endpoint
API_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"

UNSLOTH_TEMPLATE_2 = """
echo '{b64}' | base64 -d > /workspace/dataset.jsonl && \
apt update && apt install -y git python3-pip && \
pip install unsloth transformers datasets accelerate && \
python3 -m unsloth.finetune \
  --base_model {model} \
  --dataset_path /workspace/dataset.jsonl \
  --output_dir {output_dir} \
  --epochs 2 --batch_size 4 \
  --lora_r 8 --lora_alpha 16 --use_qlora False
"""

UNSLOTH_TEMPLATE = """
python3 -m unsloth.finetune \
  --base_model {model} \
  --dataset_path {dataset} \
  --output_dir {output_dir} \
  --lora_r 8 --lora_alpha 16 \
  --use_qlora False \
  --epochs 3 --batch_size 4
"""


def run_finetuning_job(job):
    print(f"Starting finetuning for job {job.id}...")

    # 1. Prepare dataset
    dataset_path = f"/app/uploads/{job.dataset_filename}"
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at {dataset_path}")    
    
    logger.info('call : create_runpod_job')
    job_id = create_runpod_job(model=job.base_model, job_id=job.id, dataset_path=dataset_path)
    logger.info(f'job_id : {job_id}')
    poll_runpod_job_status(job_id)

def create_runpod_job(model: str, job_id: str, dataset_path:str ):

    with open(dataset_path, "rb") as f:
        b64_dataset = base64.b64encode(f.read()).decode()

    script = """
    apt update && apt install -y git python3-pip && \
    pip install unsloth transformers datasets accelerate && \
    echo "{b64}" | base64 -d > /workspace/dataset.jsonl && \
    python3 -m unsloth.finetune \
    --base_model unsloth/llama-3-8b-Instruct \
    --dataset_path /workspace/dataset.jsonl \
    --output_dir /workspace/output \
    --epochs 2 --batch_size 4
    """.format(b64=b64_dataset)

    logger.info(f'before calling : {API_URL}')

    payload = {
        "input": {
            "script": script
        }
    }

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    job_id = None
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)
        
        res_json = response.json()
        logger.info(f"RunPod raw response: {res_json}")
        
        if "id" in res_json:
            job_id = res_json["id"]
            logger.info(f"✅ Job launched with ID: {job_id}")
        else:
            logger.error(f"⚠️ Unexpected response format: {res_json}")
        return job_id    
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP error: {e} — {response.text}")
    except Exception as e:
        logger.exception(f"❌ General error calling {API_URL}: {e}")


# Load HF Token from environment
HF_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
HF_USERNAME = os.getenv("HUGGING_FACE_USERNAME")

def poll_runpod_job_status(job_id, interval=30):
    """
    Polls RunPod job status every `interval` seconds and prints logs until job completes.
    """
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }

    status_query = """
    query GetJobStatus($id: ID!) {
      job(id: $id) {
        id
        status
        error
        output
        logs
      }
    }
    """

    variables = {"id": job_id}
    print(f"📡 Polling RunPod Job ID: {job_id}")

    while True:
        response = requests.post(
            RUNPOD_ENDPOINT_ID,
            headers=headers,
            json={"query": status_query, "variables": variables},
        )

        if response.status_code != 200:
            print(f"❌ Error polling job: {response.text}")
            break

        data = response.json()["data"]["job"]
        status = data["status"]
        logs = data.get("logs", "")
        error = data.get("error")

        print(f"📍 Job Status: {status}")
        if logs:
            print("📝 Logs:\n", logs[-1000:])  # Show last 1000 chars of logs

        if error:
            print("❌ Error:\n", error)
            break

        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            if status == "COMPLETED":
                print("✅ Job completed successfully.")
                output = data.get("output")
                print("📦 Output:", output)
            else:
                print(f"⚠️ Job finished with status: {status}")
            break

        time.sleep(interval)



'''
    # 4. Push to Hub
    repo_id = f"{HF_USERNAME}/{job.new_model_name}"
    print(f"Training complete. Pushing model to Hugging Face Hub at {repo_id}")
    
    # Use HfApi to create the repo first if it doesn't exist
    api = HfApi()
    api.create_repo(repo_id, token=HF_TOKEN, exist_ok=True)
    
    model.push_to_hub(repo_id, token=HF_TOKEN)
    tokenizer.push_to_hub(repo_id, token=HF_TOKEN)
    
    print("Model successfully pushed to Hub.")
'''    

