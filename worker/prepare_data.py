# prepare_data.py
import json
import base64
import os
import sys

# Assume job_params are passed as a JSON file via --params_file argument
if __name__ == "__main__":
    if "--params_file" in sys.argv:
        params_file_index = sys.argv.index("--params_file") + 1
        if params_file_index < len(sys.argv):
            params_file_path = sys.argv[params_file_index]
            try:
                with open(params_file_path, "r") as f:
                    job_params = json.load(f)
            except Exception as e:
                print(f"Error loading job parameters from {params_file_path}: {e}")
                sys.exit(1)
        else:
            print("Error: --params_file argument provided without a path.")
            sys.exit(1)
    else:
        print("Error: --params_file argument not found. Job parameters not provided.")
        sys.exit(1)

    # Expect the base64_dataset_content in the job_params
    base64_data = job_params.get("base64_dataset_content")
    if not base64_data:
        print("Error: 'base64_dataset_content' not found in job parameters.")
        sys.exit(1)

    output_path = "/workspace/dataset.jsonl" # Target path on the pod

    try:
        # Decode the base64 content
        decoded_data = base64.b64decode(base64_data)

        # Write to the specified path
        with open(output_path, "wb") as f: # Use 'wb' for binary write
            f.write(decoded_data)
        print(f"Dataset successfully written to {output_path}")

    except Exception as e:
        print(f"Error during data preparation: {e}")
        sys.exit(1)