import os
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from huggingface_hub import HfApi

# Load HF Token from environment
HF_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
HF_USERNAME = os.getenv("HUGGING_FACE_USERNAME")

# This format must match the model's template.
# Phi-3's template is <|user|>\n{question}<|end|><|assistant|>\n{answer}<|end|>
alpaca_prompt = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{}

### Response:
{}"""

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    outputs      = examples["output"]
    texts = []
    for instruction, output in zip(instructions, outputs):
        text = alpaca_prompt.format(instruction, output)
        texts.append(text)
    return { "text" : texts, }

def run_finetuning_job(job):
    print(f"Starting finetuning for job {job.id}...")

    # 1. Prepare dataset
    dataset_path = f"/app/uploads/{job.dataset_filename}"
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at {dataset_path}")
    
    # We rename columns to fit our generic prompt format
    dataset = load_dataset("csv", data_files=dataset_path, split="train")
    dataset = dataset.rename_column("question", "instruction")
    dataset = dataset.rename_column("answer", "output")

    # 2. Load Unsloth model
    max_seq_length = 2048
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=job.base_model,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=True,
        random_state=3407,
    )

    formatted_dataset = dataset.map(formatting_prompts_func, batched=True)

    # 3. Train the model
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=formatted_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=60, # Keep it short for a quick demo
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir="outputs",
        ),
    )
    trainer.train()

    # 4. Push to Hub
    repo_id = f"{HF_USERNAME}/{job.new_model_name}"
    print(f"Training complete. Pushing model to Hugging Face Hub at {repo_id}")
    
    # Use HfApi to create the repo first if it doesn't exist
    api = HfApi()
    api.create_repo(repo_id, token=HF_TOKEN, exist_ok=True)
    
    model.push_to_hub(repo_id, token=HF_TOKEN)
    tokenizer.push_to_hub(repo_id, token=HF_TOKEN)
    
    print("Model successfully pushed to Hub.")