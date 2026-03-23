import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering

# === CHANGE THIS PATH to where YOU unzipped the model ===
model_path = "."          # current directory containing config.json, pytorch_model.bin, etc.

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

print("Loading model...")
model = AutoModelForQuestionAnswering.from_pretrained(model_path)

model.eval()   # important: turn off training mode
print("Model loaded successfully!")

# Sample contract text for testing (shortened to fit within 512 tokens)
contract_text = """
SOFTWARE LICENSE AGREEMENT

PARTIES: This Agreement is between ABC Technology Inc., a Delaware corporation ("Licensor") 
and XYZ Corporation, a California corporation ("Licensee"), effective January 1, 2024.

TERM: Initial term of twelve (12) months, automatically renewing for successive twelve (12) month periods 
unless sixty (60) days written notice of non-renewal is provided.

LICENSE FEE: Annual fee of $50,000 USD, payable within thirty (30) days of invoice.

TERMINATION: Either party may terminate for cause upon thirty (30) days written notice if the other party 
materially breaches and fails to cure within the notice period.

CONFIDENTIALITY: Confidential Information protected for five (5) years following disclosure.

LIABILITY: Total liability shall not exceed fees paid in the preceding twelve (12) months.

GOVERNING LAW: This Agreement is governed by the laws of the State of Delaware.

INSURANCE: Licensee shall maintain liability insurance of at least $1,000,000 per occurrence.

NON-COMPETE: Licensee shall not develop competing software during the term and for one (1) year thereafter.

ASSIGNMENT: Neither party may assign without prior written consent, except to an affiliate or in a merger.
"""

# Good questions for signer-risk (from CUAD categories)
questions = [
    "What is the Renewal Term after the initial term expires?",
    "What is the notice period required to terminate renewal?",
    "Is there an Uncapped Liability clause?",
    "What is the Governing Law?",
    "Can a party terminate this contract without cause?",
]

def find_answer(question, context, max_len=512):
    inputs = tokenizer(
        question,
        context,
        return_tensors="pt",
        max_length=max_len,
        truncation="only_second",
        padding="max_length"
    )

    with torch.no_grad():
        outputs = model(**inputs)

    start = torch.argmax(outputs.start_logits).item()
    end = torch.argmax(outputs.end_logits).item() + 1
    
    # Ensure end is after start
    if end <= start:
        end = start + 1

    answer = tokenizer.decode(inputs["input_ids"][0][start:end], skip_special_tokens=True)
    score = (outputs.start_logits[0, start] + outputs.end_logits[0, end-1]).item()

    # More lenient filter - only reject very short or clearly wrong answers
    if len(answer.strip()) < 2 or score < -5.0:
        return None

    return {
        "question": question,
        "answer": answer.strip(),
        "confidence": round(score, 2)
    }

print("\n" + "="*60)
print("CONTRACT Q&A - Interactive Mode")
print("="*60)
print("\nContract loaded. Ask questions about it.")
print("Type 'quit' or 'exit' to stop.\n")

while True:
    question = input("Your question: ").strip()
    
    if question.lower() in ['quit', 'exit', 'q']:
        print("Goodbye!")
        break
    
    if not question:
        continue
    
    result = find_answer(question, contract_text)
    if result:
        print(f"\nAnswer: {result['answer']}")
        print(f"Confidence: {result['confidence']}\n")
    else:
        print("\nNo clear answer found in the contract.\n")