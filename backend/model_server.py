"""
Standalone model server for RoBERTa QA inference.

Run this in a dedicated terminal so the model is loaded once and reused:
    python backend/model_server.py
"""

import logging
from typing import Optional

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

from retrieval_pipeline.config import HF_MAX_LENGTH, HF_MODEL_PATH, MODEL_SERVER_BATCH_SIZE, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Contract QA Model Server",
    description="Dedicated QA inference service for contract risk analysis",
    version="1.0.0",
)


tokenizer: Optional[AutoTokenizer] = None
model: Optional[AutoModelForQuestionAnswering] = None
device: Optional[torch.device] = None


class QARequest(BaseModel):
    question: str
    context: str


class QAResponse(BaseModel):
    answer: str
    confidence: float


class QABatchRequest(BaseModel):
    requests: list[QARequest]


class QABatchResponse(BaseModel):
    responses: list[QAResponse]


def _run_qa_batch(items: list[QARequest]) -> list[QAResponse]:
    """Run QA inference for a batch of question/context pairs."""
    if tokenizer is None or model is None or device is None:
        return [QAResponse(answer="", confidence=-999.0) for _ in items]

    questions = [item.question for item in items]
    contexts = [item.context for item in items]

    inputs = tokenizer(
        questions,
        contexts,
        return_tensors="pt",
        max_length=HF_MAX_LENGTH,
        truncation="only_second",
        padding="max_length",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    responses: list[QAResponse] = []
    for i in range(len(items)):
        start = torch.argmax(outputs.start_logits[i]).item()
        end = torch.argmax(outputs.end_logits[i]).item() + 1
        if end <= start:
            end = start + 1

        answer = tokenizer.decode(inputs["input_ids"][i][start:end], skip_special_tokens=True)
        confidence = (outputs.start_logits[i, start] + outputs.end_logits[i, end - 1]).item()
        responses.append(QAResponse(answer=answer.strip(), confidence=round(confidence, 2)))

    return responses


@app.on_event("startup")
def load_model() -> None:
    """Load tokenizer/model once during service startup."""
    global tokenizer, model, device

    logger.info("Loading model server resources from %s", HF_MODEL_PATH)
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_PATH, local_files_only=True, use_fast=False)
    model = AutoModelForQuestionAnswering.from_pretrained(HF_MODEL_PATH, local_files_only=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    logger.info("Model server ready on %s", device)


@app.get("/health")
def health() -> dict:
    """Service readiness probe."""
    ready = tokenizer is not None and model is not None and device is not None
    return {"status": "ok" if ready else "loading"}


@app.post("/qa", response_model=QAResponse)
def qa_inference(payload: QARequest) -> QAResponse:
    """Run one QA inference request."""
    return _run_qa_batch([payload])[0]


@app.post("/qa_batch", response_model=QABatchResponse)
def qa_batch_inference(payload: QABatchRequest) -> QABatchResponse:
    """Run batched QA inference with chunking for memory stability."""
    if not payload.requests:
        return QABatchResponse(responses=[])

    batch_size = max(1, MODEL_SERVER_BATCH_SIZE)
    all_responses: list[QAResponse] = []

    for start in range(0, len(payload.requests), batch_size):
        chunk = payload.requests[start:start + batch_size]
        all_responses.extend(_run_qa_batch(chunk))

    return QABatchResponse(responses=all_responses)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
