"""
Helper script to download and save a base model for testing the local reasoning pipeline.
Run this script if you do not have your own fine-tuned model ready yet.
"""
import os
import shutil
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def setup_local_model(model_name="roberta-base", output_dir="./fine_tuned_model"):
    print(f"Downloading {model_name}...")
    
    if os.path.exists(output_dir):
        print(f"Warning: {output_dir} already exists.")
        choice = input("Overwrite? (y/n): ")
        if choice.lower() != 'y':
            print("Aborting.")
            return
        shutil.rmtree(output_dir)

    # Download and save tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.save_pretrained(output_dir)
    
    # Download and save model (initialized with 3 labels for Low/Medium/High)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=3,
        id2label={0: "LOW", 1: "MEDIUM", 2: "HIGH"},
        label2id={"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    )
    model.save_pretrained(output_dir)
    
    print(f"\nSuccess! Model saved to {output_dir}")
    print("You can now run the analysis system.")

if __name__ == "__main__":
    setup_local_model()
