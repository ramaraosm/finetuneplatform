# finetune_template.py
import argparse
import os
import json
import sys
import torch
from unsloth import FastLanguageModel
from transformers import TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset
from huggingface_hub import HfApi, login, create_repo # Import HfApi, login, create_repo
# Assuming you have transformers and other libraries installed by Unsloth
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import PeftModel, LoraConfig # For adapter models

# --- Helper function for prompt formatting ---
ALPACA_PROMPT = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""
EOS_TOKEN = None

def formatting_prompts_func(examples, tokenizer_instance):
    global EOS_TOKEN
    if EOS_TOKEN is None:
        EOS_TOKEN = tokenizer_instance.eos_token
    instructions = examples["instruction"]
    inputs = examples["input"]
    outputs = examples["output"]
    texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        if input_text:
            text = ALPACA_PROMPT.format(instruction, input_text, output) + EOS_TOKEN
        else:
            text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}" + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }

if __name__ == "__main__":
    print(f"Executing dynamic fine-tuning script")
    parser = argparse.ArgumentParser(description="Dynamic Unsloth Fine-tuning Script")
    parser.add_argument("--params_file", type=str, required=True,
                        help="Path to a JSON file containing job parameters.")
    args = parser.parse_args()

    # Load parameters from the provided JSON file
    with open(args.params_file, 'r') as f:
        params = json.load(f)

    # Extract parameters from the loaded JSON
    base_model = params.get("base_model", "unsloth/llama-3-8b-Instruct")
    dataset_path = params.get("dataset_path", "/workspace/dataset.jsonl")
    output_dir = params.get("output_dir", "/workspace/output")
    epochs = params.get("epochs", 2)
    batch_size = params.get("batch_size", 4)
    learning_rate = params.get("learning_rate", 2e-4)
    gradient_accumulation_steps = params.get("gradient_accumulation_steps", 4)

    print(f"Executing dynamic fine-tuning script with parameters: {params}")

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset NOT found at: {dataset_path}. Please ensure it's uploaded to your volume.")
        exit(1)
    else:
        print(f"Dataset found at: {dataset_path}")

    try:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name = base_model, max_seq_length = 2048, dtype = None, load_in_4bit = True,
        )
        model = FastLanguageModel.get_peft_model(
            model, r = 16, target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",],
            lora_alpha = 16, lora_dropout = 0, bias = "none", use_gradient_checkpointing = "unsloth", random_state = 3407,
        )
        print("Model and tokenizer loaded and LoRA adapters applied.")

        dataset = load_dataset("json", data_files=dataset_path, split="train")
        dataset = dataset.map(lambda examples: formatting_prompts_func(examples, tokenizer), batched = True,)
        print(f"Dataset loaded and formatted. First example: {dataset[0]['text'][:500]}...")

        training_args = TrainingArguments(
            per_device_train_batch_size = batch_size, gradient_accumulation_steps = gradient_accumulation_steps,
            warmup_steps = int(0.03 * epochs * len(dataset) / (batch_size * gradient_accumulation_steps)),
            num_train_epochs = float(epochs), learning_rate = learning_rate,
            fp16 = not torch.cuda.is_bf16_supported(), bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = 10, optim = "adamw_8bit", weight_decay = 0.01,
            lr_scheduler_type = "linear", seed = 3407, output_dir = output_dir,
            report_to = "none", save_strategy="epoch", save_total_limit=1,
        )

        trainer = SFTTrainer(
            model = model, tokenizer = tokenizer, train_dataset = dataset,
            dataset_text_field = "text", max_seq_length = 2048, args = training_args,
        )

        print(f"Starting training for {epochs} epochs...")
        trainer.train()
        print("Training completed.")

        save_path_adapters = os.path.join(output_dir, "finetuned_adapters")
        trainer.model.save_pretrained(save_path_adapters)
        tokenizer.save_pretrained(save_path_adapters)
        print(f"LoRA adapters saved to: {save_path_adapters}")

        print("Dynamic fine-tuning process finished successfully.")

        # --- Hugging Face specific parameters ---
        # Example repo ID: "your-hf-username/your-model-name"
        # It's good practice to make this a parameter passed via job_params
        hf_repo_id = params.get("hf_repo_id", "")
        # Set to True for private repo, False for public
        hf_private_repo = params.get("hf_private_repo", False)
        # Optional: message for the commit
        hf_commit_message = params.get("hf_commit_message", "Fine-tuned model with Unsloth on RunPod")
        # --- PUSH TO HUGGING FACE HUB ---
        print(f"\n--- Pushing Model to Hugging Face Hub ({hf_repo_id}) ---")

        # 1. Log in to Hugging Face Hub using the HF_TOKEN environment variable
        # This will automatically pick up the token if set in env vars.
        # It's good practice to explicitly check if token is there.
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            login(token=hf_token)
            print("Successfully logged into Hugging Face Hub.")
        else:
            print("HF_TOKEN environment variable not found. Cannot push to Hugging Face Hub.")
            sys.exit(1)

        # 2. Initialize HfApi client (optional, but useful for advanced operations)
        api = HfApi()

        # 3. Create the repository if it doesn't exist
        # This is robust because it won't fail if the repo already exists.
        try:
            api.create_repo(repo_id=hf_repo_id, private=hf_private_repo, exist_ok=True)
            print(f"Hugging Face repository '{hf_repo_id}' ensured.")
        except Exception as e:
            print(f"Error creating/ensuring HF repo: {e}")
            sys.exit(1)
            
        # 4. Push the model and tokenizer from the output_dir
        # For PEFT models (like Unsloth), model.push_to_hub automatically handles adapters.
        # You'll need to re-load the model and tokenizer if they are not active in memory after training.
        # Ensure you use the correct AutoClasses for your model type.
        try:
            # Load the model and tokenizer from the saved output_dir
            # This is critical after model.save_pretrained() if the 'model' object isn't the final one
            print(f"Loading model and tokenizer from {output_dir} for push...")
            final_tokenizer = AutoTokenizer.from_pretrained(output_dir+"/finetuned_adapters")
            
            # For Unsloth, you typically save the PEFT model.
            # You might need to load the base model first and then load the adapter weights.
            # However, the `from_pretrained` method of PEFT models usually handles this.
            # The most straightforward way is to use the `push_to_hub` method from `model` itself,
            # which correctly pushes adapters and the tokenizer if they were created by PEFT.
            
            # --- For PEFT/Unsloth Models, it's often more direct: ---
            # Reload your fine-tuned model (e.g., via Unsloth's FastLanguageModel for pushing)
            # Example (assuming you have Unsloth loaded):
            # model_to_push, tokenizer_to_push = FastLanguageModel.from_pretrained(
            #     model_name=None, # No pre-trained model needed, load from path
            #     max_seq_length=..., # Your original max_seq_length
            #     dtype=..., # Your original dtype
            #     load_in_4bit=..., # Your original quantization
            #     token=hf_token, # Pass token if needed for loading base model
            #     # Load adapter weights
            #     local_model_path=output_dir,
            # )
            trainer.model.push_to_hub(hf_repo_id, token=hf_token, commit_message=hf_commit_message)
            final_tokenizer.push_to_hub(hf_repo_id, token=hf_token) # Tokenizer also gets pushed

            # A more generic way using transformers, which should work if output_dir
            # contains all necessary files (including adapter config for PEFT models)
            # Ensure the correct AutoClass is used based on your model type (e.g., LlamaForCausalLM, MistralForCausalLM)
            # If you are saving only adapters, you might load the base model first, then add adapter weights.
            
            # If your `output_dir` contains `adapter_config.json` and `adapter_model.bin`
            # along with `tokenizer.json` and `special_tokens_map.json` etc.
            # then you can use `api.upload_folder`.
            '''
            api.upload_folder(
                folder_path=output_dir,
                repo_id=hf_repo_id,
                repo_type="model",
                commit_message=hf_commit_message,
                token=hf_token, # Explicitly pass token if needed
                # ignore_patterns=["*.pt", "*.bin"] if you only want to push certain files
            )
            '''
            print(f"Model and adapters successfully pushed to https://huggingface.co/{hf_repo_id}")

        except Exception as e:
            print(f"Error pushing model to Hugging Face Hub: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"Dynamic fine-tuning failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)