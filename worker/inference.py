# First, uninstall existing PyTorch (important to avoid conflicts)
#!pip uninstall torch torchvision torchaudio -y

# Then, install the latest stable version.
# For CUDA: (replace cu121 with your CUDA version, e.g., cu118, cu124)
#!pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# For CPU-only:
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

#!pip install --upgrade transformers peft accelerate bitsandbytes


from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig
import torch
import gc # Import the garbage collector module

# 1. Define the path to your fine-tuned model
peft_model_id = "ramaraohface/llama-finetuned38"

# --- Determine the device to use ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Initialize model and tokenizer outside the try block for better scope control
model = None
tokenizer = None
config = None

try:
    # 2. Load the PEFT configuration
    config = PeftConfig.from_pretrained(peft_model_id)
    base_model_name = config.base_model_name_or_path

    # 3. Load the original base model and move it to the determined device
    model = AutoModelForCausalLM.from_pretrained(base_model_name).to(device)
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    # 4. Load the PEFT adapter and merge it with the base model
    model = PeftModel.from_pretrained(model, peft_model_id)

    print("PEFT model and tokenizer loaded successfully!")
    print(f"Base model used: {base_model_name}")
    print(f"Model type: {type(model)}")
    print(f"Model device: {model.device}")

    # Now you can use the model for inference
    prompt = "give me different game names played by childeren in remote villages in Andharapradesh in India."
    inputs = tokenizer(prompt, return_tensors="pt")

    # Move all input tensors to the same device as the model
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Generate text
    outputs = model.generate(**inputs, max_new_tokens=100, num_return_sequences=1)
    print("\n--- Generated Text ---")
    print(tokenizer.decode(outputs[0], skip_special_tokens=True))

except ImportError as e:
    print(f"ImportError: {e}")
    print("This usually means your transformers, peft, or torch libraries are not compatible or too old.")
    print("Please ensure you have the latest versions installed:")
    print("pip install --upgrade transformers peft accelerate torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121") # Adjust for your CUDA/CPU setup
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc() # Print full traceback for more detailed error info
    print("Please double-check the model ID and ensure all dependencies are correctly installed and up-to-date.")

finally:
    # --- Memory Clearing Steps (after model usage or in case of error) ---
    print("\n--- Attempting to clear GPU memory ---")

    # 1. Delete references to large objects
    if 'model' in locals() and model is not None:
        del model
    if 'tokenizer' in locals() and tokenizer is not None:
        del tokenizer
    if 'config' in locals() and config is not None:
        del config
    if 'inputs' in locals() and inputs is not None:
        del inputs # Delete the input tensors if they are still around
    if 'outputs' in locals() and outputs is not None:
        del outputs # Delete the output tensors

    # 2. Run Python's garbage collector
    gc.collect()

    # 3. Clear PyTorch's CUDA memory cache (if using GPU)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("CUDA memory cache cleared.")
    else:
        print("Not using CUDA, no cache to clear.")

    print("Memory clearing attempt finished.")