"""
LLM Reasoner — local RoBERTa QA-based risk analysis for Legal Contract Risk Analyzer.

Pipeline:
  1. Extract & filter Pinecone matches above similarity threshold.
  2. Run RoBERTa QA against the clause for HIGH / MEDIUM / LOW indicator questions.
  3. Build a human-readable explanation from whatever evidence was found.
  4. Always return a non-empty explanation and a definitive risk level (HIGH/MEDIUM/LOW).
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

from .config import (
    HF_BATCH_SIZE,
    HF_MAX_LENGTH,
    HF_MODEL_PATH,
    REASONER_SIMILARITY_THRESHOLD,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton model cache
# ---------------------------------------------------------------------------
_tokenizer = None
_model = None
_device = None

# ---------------------------------------------------------------------------
# Risk-indicator questions per level
# ---------------------------------------------------------------------------
QUESTIONS: Dict[str, List[str]] = {
    "HIGH": [
        "Is there an Uncapped Liability clause?",
        "Can a party terminate this contract without cause?",
        "Is there a non-compete obligation?",
    ],
    "MEDIUM": [
        "What is the Renewal Term after the initial term expires?",
        "What is the notice period required to terminate renewal?",
    ],
    "LOW": [
        "What is the Governing Law?",
        "What are the Insurance requirements?",
    ],
}

# Human-friendly label for each question key
QUESTION_LABELS: Dict[str, str] = {
    "Is there an Uncapped Liability clause?": "uncapped liability provision",
    "Can a party terminate this contract without cause?": "termination without cause right",
    "Is there a non-compete obligation?": "non-compete obligation",
    "What is the Renewal Term after the initial term expires?": "auto-renewal term",
    "What is the notice period required to terminate renewal?": "renewal termination notice period",
    "What is the Governing Law?": "governing law",
    "What are the Insurance requirements?": "insurance requirements",
}


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def _load_llm() -> Tuple[AutoTokenizer, AutoModelForQuestionAnswering, torch.device]:
    """Load tokenizer/model once and cache them for reuse."""
    global _tokenizer, _model, _device

    if _tokenizer is not None and _model is not None and _device is not None:
        return _tokenizer, _model, _device

    model_path = HF_MODEL_PATH
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Local model path not found: {model_path}.")

    logger.info("Loading local QA risk reasoning model from %s", model_path)

    _tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, use_fast=False)
    _model = AutoModelForQuestionAnswering.from_pretrained(model_path, local_files_only=True)

    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model.to(_device)
    _model.eval()

    logger.info("Loaded local QA model on %s", _device)
    return _tokenizer, _model, _device


# ---------------------------------------------------------------------------
# Match extraction helpers
# ---------------------------------------------------------------------------

def _extract_matches(retrieved_clauses: Any) -> List[Dict[str, Any]]:
    """Normalize Pinecone query results into plain dicts."""
    if isinstance(retrieved_clauses, list):
        raw_matches = retrieved_clauses
    elif hasattr(retrieved_clauses, "matches"):
        raw_matches = retrieved_clauses.matches
    elif isinstance(retrieved_clauses, dict) and "matches" in retrieved_clauses:
        raw_matches = retrieved_clauses["matches"]
    else:
        raw_matches = []

    normalized: List[Dict[str, Any]] = []
    for match in raw_matches:
        score = float(
            match.get("score", 0.0) if isinstance(match, dict) else getattr(match, "score", 0.0)
        )
        metadata = (
            match.get("metadata", {}) if isinstance(match, dict) else getattr(match, "metadata", {})
        )

        text = metadata.get("clause_text") or metadata.get("text") or ""
        normalized.append(
            {
                "text": text[:200] + "..." if len(text) > 200 else text,
                "severity": str(metadata.get("severity", "unknown")).upper(),
                "clause_type": str(metadata.get("clause_type", "unknown")),
                "score": round(score, 4),
            }
        )
    return normalized


def _filter_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep only matches above the similarity threshold, sorted by score desc."""
    return sorted(
        [m for m in matches if m.get("score", 0.0) >= REASONER_SIMILARITY_THRESHOLD],
        key=lambda i: i["score"],
        reverse=True,
    )


# ---------------------------------------------------------------------------
# QA inference
# ---------------------------------------------------------------------------

def _find_answer(question: str, context: str) -> Optional[Dict[str, Any]]:
    """Run one QA inference. Returns None when the model gives no confident answer."""
    tokenizer, model, device = _load_llm()
    inputs = tokenizer(
        question,
        context,
        return_tensors="pt",
        max_length=HF_MAX_LENGTH,
        truncation="only_second",
        padding="max_length",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    start = torch.argmax(outputs.start_logits).item()
    end = torch.argmax(outputs.end_logits).item() + 1
    if end <= start:
        end = start + 1

    answer = tokenizer.decode(inputs["input_ids"][0][start:end], skip_special_tokens=True)
    score = (outputs.start_logits[0, start] + outputs.end_logits[0, end - 1]).item()

    if len(answer.strip()) < 2 or score < -5.0:
        return None

    return {"answer": answer.strip(), "confidence": round(score, 2)}


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze_clause_with_llm(clause_text: str, retrieved_clauses: Any) -> Dict[str, Any]:
    """
    Analyze a single clause and always return a meaningful risk assessment.

    Returns a dict with keys:
        clause_text, risk_level, explanation, similar_clauses
    """
    all_matches = _extract_matches(retrieved_clauses)
    similar_clauses = _filter_matches(all_matches)

    risk_level: str = "UNKNOWN"
    highest_level_found: Optional[str] = None
    found_indicators: List[str] = []

    # --- Step 1: QA-based risk detection ---
    for level in ["HIGH", "MEDIUM", "LOW"]:
        for question in QUESTIONS[level]:
            res = _find_answer(question, clause_text)
            if res:
                label = QUESTION_LABELS.get(question, question)
                found_indicators.append(f"{label}")
                if highest_level_found is None:
                    highest_level_found = level

    # --- Build explanation ---
    if highest_level_found:
        risk_level = highest_level_found
        indicators_str = ", ".join(found_indicators[:3])  # max 3 indicators shown
        explanation = f"This clause contains: {indicators_str}."

    # --- Step 2: Pinecone similarity fallback ---
    elif similar_clauses:
        top = similar_clauses[0]
        sev = top["severity"]
        risk_level = sev if sev in ("HIGH", "MEDIUM", "LOW") else "LOW"
        pct = round(top["score"] * 100, 1)
        explanation = (
            f"This clause is {pct}% similar to a known {risk_level} risk "
            f"\"{top['clause_type']}\" clause in the knowledge base."
        )
    else:
        risk_level = "LOW"
        explanation = "No risk patterns detected. This clause appears to be standard boilerplate."

    return {
        "clause_text": clause_text,
        "risk_level": risk_level,
        "explanation": explanation,
        "similar_clauses": similar_clauses,
    }


def analyze_clauses_with_llm_batch(
    contract_clauses: List[str], query_results_list: List[Any]
) -> List[Dict[str, Any]]:
    """Analyze a batch of clauses sequentially."""
    return [
        analyze_clause_with_llm(c, r)
        for c, r in zip(contract_clauses, query_results_list)
    ]
