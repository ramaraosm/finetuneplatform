import time
import os

# These are not used for finetuning but show that we have access to the job details
HF_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
HF_USERNAME = os.getenv("HUGGING_FACE_USERNAME")

def run_mock_finetuning_job(job):
    """
    Simulates a finetuning job without using a GPU.
    """
    print("--- RUNNING IN CPU MOCK MODE ---")
    print(f"Received job {job.id} to 'finetune' model {job.base_model}")
    print(f"Dataset: {job.dataset_filename}")
    
    # Simulate the download and model loading
    print("Simulating model and data loading...")
    time.sleep(5)
    
    # Simulate the training process
    print("Simulating finetuning training loop... (will take ~30 seconds)")
    for i in range(10):
        print(f"Mock training step {i+1}/10...")
        time.sleep(3)
    
    # Simulate pushing to hub
    repo_id = f"{HF_USERNAME}/{job.new_model_name}"
    print(f"Simulation complete. Mock model would be pushed to {repo_id}")
    time.sleep(2)
    
    print(f"Mock job {job.id} completed successfully.")
    # In a real scenario, this mock worker would NOT push to the hub.