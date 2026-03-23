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
        raise FileNotFoundError(
            f"Local model path not found: {model_path}.\n"
            "Please set HF_MODEL_PATH to the correct location. Available candidates:\n"
            f"  - {os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'roberta-base'))}\n"
            f"  - {os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'roberta-base'))}\n"
            f"  - current HF_MODEL_PATH environment value: {os.getenv('HF_MODEL_PATH', '<not set>')}"
        )

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


def summarize_contract_analysis(analyses: List[Dict[str, Any]]) -> str:
    """
    Generate a comprehensive summary of the contract analysis results.
    
    This function takes the individual clause analyses and creates an overall
    summary of the document's risk profile, key findings, and recommendations.
    
    Args:
        analyses: List of clause analysis results from analyze_clauses_with_llm_batch
        
    Returns:
        A human-readable summary string
    """
    if not analyses:
        return "No clauses were analyzed. Unable to generate summary."
    
    # Count risk levels
    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    high_risk_clauses = []
    medium_risk_clauses = []
    
    for analysis in analyses:
        risk_level = analysis.get("risk_level", "UNKNOWN")
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        if risk_level == "HIGH":
            high_risk_clauses.append(analysis.get("clause_text", "")[:100] + "...")
        elif risk_level == "MEDIUM":
            medium_risk_clauses.append(analysis.get("clause_text", "")[:100] + "...")
    
    total_clauses = len(analyses)
    
    # Build summary
    summary_parts = []
    summary_parts.append(f"## Contract Analysis Summary\n")
    summary_parts.append(f"**Total Clauses Analyzed:** {total_clauses}\n")
    summary_parts.append(f"**Risk Distribution:**")
    summary_parts.append(f"- High Risk: {risk_counts['HIGH']} ({risk_counts['HIGH']/total_clauses*100:.1f}%)")
    summary_parts.append(f"- Medium Risk: {risk_counts['MEDIUM']} ({risk_counts['MEDIUM']/total_clauses*100:.1f}%)")
    summary_parts.append(f"- Low Risk: {risk_counts['LOW']} ({risk_counts['LOW']/total_clauses*100:.1f}%)")
    summary_parts.append(f"- Unknown: {risk_counts['UNKNOWN']} ({risk_counts['UNKNOWN']/total_clauses*100:.1f}%)\n")
    
    # Overall assessment
    if risk_counts['HIGH'] > total_clauses * 0.2:  # More than 20% high risk
        overall_risk = "HIGH"
        assessment = "This contract contains significant risk factors that require careful review."
    elif risk_counts['HIGH'] + risk_counts['MEDIUM'] > total_clauses * 0.3:  # More than 30% medium/high
        overall_risk = "MEDIUM"
        assessment = "This contract has moderate risk factors that should be evaluated."
    else:
        overall_risk = "LOW"
        assessment = "This contract appears to have standard risk levels."
    
    summary_parts.append(f"**Overall Risk Assessment:** {overall_risk}")
    summary_parts.append(f"{assessment}\n")
    
    # Key findings
    summary_parts.append("**Key Findings:**")
    if high_risk_clauses:
        summary_parts.append(f"- **Critical Issues:** {len(high_risk_clauses)} high-risk clauses identified")
        for i, clause in enumerate(high_risk_clauses[:3]):  # Show up to 3 examples
            summary_parts.append(f"  {i+1}. {clause}")
        if len(high_risk_clauses) > 3:
            summary_parts.append(f"  ... and {len(high_risk_clauses) - 3} more")
    
    if medium_risk_clauses:
        summary_parts.append(f"- **Notable Concerns:** {len(medium_risk_clauses)} medium-risk clauses identified")
    
    # Recommendations
    summary_parts.append("\n**Recommendations:**")
    if overall_risk == "HIGH":
        summary_parts.append("- Seek legal counsel for review of high-risk clauses")
        summary_parts.append("- Consider renegotiating problematic terms")
        summary_parts.append("- Document all concerns and mitigation strategies")
    elif overall_risk == "MEDIUM":
        summary_parts.append("- Review medium-risk clauses with legal team")
        summary_parts.append("- Ensure proper monitoring and compliance mechanisms")
        summary_parts.append("- Consider adding protective language where possible")
    else:
        summary_parts.append("- Contract appears acceptable with standard review")
        summary_parts.append("- Monitor for any changes in business circumstances")
    
    summary_parts.append("- Maintain clear communication with all parties")
    summary_parts.append("- Keep detailed records of all contract-related activities")
    
    return "\n".join(summary_parts)
