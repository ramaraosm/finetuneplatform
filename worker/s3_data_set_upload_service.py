import boto3
import os
import base64
from dotenv import load_dotenv
from shared.utils import logger

logger = logger.setup_logger('UploadDataSetToS3')

# Load environment variables from .env file
load_dotenv()

# --- RunPod S3 Configuration ---
RUNPOD_S3_ENDPOINT_URL = os.getenv("RUNPOD_S3_ENDPOINT_URL") # IMPORTANT: Change to your datacenter's endpoint
RUNPOD_S3_ACCESS_KEY_ID = os.getenv("RUNPOD_S3_ACCESS_KEY_ID")  # From step 2.2
RUNPOD_S3_SECRET_ACCESS_KEY = os.getenv("RUNPOD_S3_SECRET_ACCESS_KEY") # From step 2.2
NETWORK_VOLUME_ID = os.getenv("NETWORK_VOLUME_ID")                       # Your Network Volume ID
region_name= os.getenv("region_name")

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=RUNPOD_S3_ENDPOINT_URL,
    aws_access_key_id=RUNPOD_S3_ACCESS_KEY_ID,
    aws_secret_access_key=RUNPOD_S3_SECRET_ACCESS_KEY,
    # region_name: Can be left blank or set to a placeholder like 'us-east-1'
    # RunPod S3 compatible API does not use AWS regions in the traditional sense.
    region_name=region_name
)

def upload_file_to_runpod_s3(local_file_path, s3_object_key):
    """
    Uploads a file to your RunPod Network Volume via S3-compatible API.
    :param local_file_path: Path to the file on your local machine.
    :param s3_object_key: The desired path/name for the file on the Network Volume.
                            e.g., "datasets/user_data/my_dataset.jsonl"
    """
    try:
        s3_client.upload_file(local_file_path, NETWORK_VOLUME_ID, s3_object_key)
        logger.info(f"Successfully uploaded {local_file_path} to s3://{NETWORK_VOLUME_ID}/{s3_object_key}")
    except Exception as e:
        logger.info(f"Error uploading file: {e}")

def list_files_in_runpod_s3(prefix=''):
    """
    Lists files in your RunPod Network Volume.
    :param prefix: Optional prefix to filter files.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=NETWORK_VOLUME_ID, Prefix=prefix)
        if 'Contents' in response:
            logger.info(f"\nFiles in s3://{NETWORK_VOLUME_ID}/{prefix}:")
            for obj in response['Contents']:
                logger.info(f"- {obj['Key']} (Size: {obj['Size']} bytes)")
        else:
            logger.info(f"No objects found in s3://{NETWORK_VOLUME_ID}/{prefix}")
    except Exception as e:
        logger.info(f"Error listing files: {e}")

def upload_data_set_to_s3(job):
    # Read data set from user uploaded data
    DATASET_PATH = f"/app/uploads/{job.dataset_filename}"
    S3_DATASET_PATH =  f"workspace/datasets/{job.id}_{job.dataset_filename}"
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Fine-tune script '{DATASET_PATH}' not found.")
        exit(1)

    upload_file_to_runpod_s3(DATASET_PATH, S3_DATASET_PATH)

    # 3. List files to verify
    list_files_in_runpod_s3(prefix=f"workspace/")


def delete_all_objects_in_network_volume(volume_id, prefix=''):
    """
    Deletes all objects (or objects within a specific prefix) from a RunPod Network Volume
    using its S3-compatible API.

    :param volume_id: The ID of your RunPod Network Volume (acts as the bucket name).
    :param prefix: Optional. A prefix to limit deletion to objects within a specific "folder".
                   e.g., 'user_data/' to delete only files in the 'user_data' directory.
    """
    print(f"Attempting to delete objects from RunPod Network Volume: '{volume_id}' with prefix: '{prefix}'")

    objects_to_delete = []
    paginator = s3_client.get_paginator('list_objects_v2')

    try:
        # List all objects in the volume (or under the specified prefix)
        pages = paginator.paginate(Bucket=volume_id, Prefix=prefix)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
        
        if not objects_to_delete:
            print("No objects found to delete.")
            return

        print(f"Found {len(objects_to_delete)} objects to delete.")

        # Delete objects in batches of up to 1000
        # The delete_objects method can take up to 1000 keys at once
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i:i + 1000]
            
            print(f"Deleting batch {int(i/1000) + 1} of {len(batch)} objects...")
            response = s3_client.delete_objects(
                Bucket=volume_id,
                Delete={
                    'Objects': batch,
                    'Quiet': True # Set to False for more detailed response about each deletion
                }
            )
            
            if 'Errors' in response:
                print(f"Errors encountered during deletion in batch {int(i/1000) + 1}:")
                for error in response['Errors']:
                    print(f"  Key: {error['Key']}, Code: {error['Code']}, Message: {error['Message']}")
            elif 'Deleted' in response:
                print(f"  Successfully deleted {len(response['Deleted'])} objects in this batch.")

        print("Deletion process completed.")

    except Exception as e:
        print(f"An error occurred during deletion: {e}")    


if __name__ == "__main__":
    # Example Usage:
    # 1. Create a dummy file for testing
    dummy_file_name = "test_dataset.jsonl"
    with open(dummy_file_name, "w") as f:
        f.write('{"instruction": "test", "input": "", "output": "test output"}\n')
        f.write('{"instruction": "test2", "input": "input2", "output": "output2"}\n')

    # 2. Upload the dummy file
    # This will be saved as /user_uploaded_datasets/test_dataset.jsonl on your Network Volume
    upload_file_to_runpod_s3(dummy_file_name, f"user_uploaded_datasets/{dummy_file_name}")

    # 3. List files to verify
    list_files_in_runpod_s3(prefix="user_uploaded_datasets/")

    # Clean up dummy file
    os.remove(dummy_file_name)