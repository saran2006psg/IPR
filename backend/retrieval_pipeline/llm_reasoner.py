"""
LLM Reasoner — local RoBERTa QA-based risk analysis for Legal Contract Risk Analyzer.

Pipeline:
  1. Extract & filter Pinecone matches above similarity threshold.
  2. Run RoBERTa QA against the clause for HIGH / MEDIUM / LOW indicator questions.
  3. Build a human-readable explanation from whatever evidence was found.
  4. Always return a non-empty explanation and a definitive risk level (HIGH/MEDIUM/LOW).
"""

import logging
import json
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .config import (
    MODEL_SERVER_DOWN_COOLDOWN_SEC,
    MODEL_SERVER_BATCH_SIZE,
    MODEL_SERVER_ENABLED,
    MODEL_SERVER_MAX_RETRIES,
    MODEL_SERVER_RETRY_BACKOFF_SEC,
    MODEL_SERVER_TIMEOUT_SEC,
    MODEL_SERVER_URL,
    QA_BATCH_MODE_ENABLED,
    REASONER_SIMILARITY_THRESHOLD,
    MIN_ANSWER_LENGTH,
    SUMMARY_MIN_CONFIDENCE,
)

logger = logging.getLogger(__name__)
_model_service_unavailable = False
_model_service_down_until = 0.0

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
                "text": text,
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
# Answer Quality Validation (Phase 1)
# ---------------------------------------------------------------------------

def _is_incomplete_answer(answer: str) -> bool:
    """Detect if answer is likely a truncated/incomplete span.
    
    Examples of incomplete answers:
    - Starts with conjunctions: "and", "or", "but"
    - Ends with open paren: "("
    - Obvious mid-word cutoff patterns
    """
    if not answer:
        return True
    
    answer_lower = answer.lower().strip()
    
    # Reject if starts with conjunctions (likely middle of sentence)
    if any(answer_lower.startswith(conj + " ") for conj in ["and", "or", "but", "the ", "a "]):
        return True
    
    # Reject if ends with open paren or comma (incomplete thought)
    if answer.rstrip().endswith(("(", ",", ";")):
        return True
    
    # Reject if very short and lowercase (likely fragment)
    if len(answer) <= 3 and answer_lower == answer:
        return True
    
    return False


def _score_answer_quality(answer: str, confidence: float) -> float:
    """Score answer quality from 0.0 (bad) to 1.0 (excellent).
    
    Considers:
    - Confidence score (normalized to 0-1 range, expected range -5 to +5)
    - Answer length (longer is better, but diminishing returns)
    - Completeness (penalize if likely truncated)
    - Capitalization (proper answers usually capitalized)
    
    Returns: float in [0.0, 1.0] range.
    """
    if not answer or len(answer.strip()) < MIN_ANSWER_LENGTH:
        return 0.0
    
    answer_clean = answer.strip()
    
    # Penalize incomplete answers
    if _is_incomplete_answer(answer_clean):
        return 0.1
    
    # Normalize confidence from expected range (-5, +5) to (0, 1)
    # confidence -1 → 0.2, confidence 0 → 0.5, confidence +1 → 0.8, confidence +2 → 0.95
    confidence_normalized = max(0.0, min(1.0, (confidence + 5.0) / 10.0))
    
    # Length factor: prefer 20-150 chars, penalize very short or very long
    length_score = min(1.0, len(answer_clean) / 150.0)
    if len(answer_clean) < 10:
        length_score *= 0.5  # Penalize very short answers
    
    # Capitalization factor: proper answers usually start with capital or quote
    cap_score = 0.9 if (answer_clean[0].isupper() or answer_clean[0] in '"\'') else 0.7
    
    # Weighted combination
    quality = (
        0.5 * confidence_normalized +  # Confidence is primary signal
        0.3 * length_score +            # Length provides context quality hint
        0.2 * cap_score                 # Capitalization is weakest signal
    )
    
    return round(quality, 2)


def _normalize_answer(answer: str) -> str:
    """Clean and normalize extracted answer, removing common artifacts.
    
    - Strip whitespace
    - Remove leading/trailing fragments: "and ", "or ", etc.
    - Collapse multiple spaces
    """
    answer = answer.strip()
    
    # Remove leading conjunctions/articles that indicate truncation
    leading_prefixes = ["and ", "or ", "but ", "the ", "a "]
    while any(answer.lower().startswith(p) for p in leading_prefixes):
        for prefix in leading_prefixes:
            if answer.lower().startswith(prefix):
                answer = answer[len(prefix):].strip()
                break
    
    # Collapse multiple spaces
    answer = re.sub(r"\s+", " ", answer)
    
    return answer


# ---------------------------------------------------------------------------
# QA inference
# ---------------------------------------------------------------------------

def _query_model_server(question: str, context: str) -> Optional[Dict[str, Any]]:
    """Call external QA model server and return answer payload."""
    global _model_service_unavailable, _model_service_down_until

    if not MODEL_SERVER_ENABLED:
        _model_service_unavailable = True
        return None

    if _model_service_unavailable and time.time() < _model_service_down_until:
        return None

    payload = json.dumps({"question": question, "context": context}).encode("utf-8")
    request = urllib.request.Request(
        MODEL_SERVER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    for attempt in range(MODEL_SERVER_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=MODEL_SERVER_TIMEOUT_SEC) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            _model_service_unavailable = False
            _model_service_down_until = 0.0

            answer = str(response_data.get("answer", "")).strip()
            confidence = float(response_data.get("confidence", -999.0))

            # PHASE 1: Stricter validation with quality scoring
            if len(answer) < MIN_ANSWER_LENGTH:  # Changed from < 2
                return None
            if confidence < -1.0:  # Changed from < -5.0 (much stricter)
                return None
            
            quality_score = _score_answer_quality(answer, confidence)
            if quality_score < 0.3:  # Reject low-quality answers even if confidence threshold passed
                logger.debug(f"Answer rejected due to low quality score {quality_score}: {answer[:50]}")
                return None
            
            answer = _normalize_answer(answer)  # Clean up fragments
            logger.debug(f"PHASE 1: Accepted answer (conf={confidence:.2f}, quality={quality_score:.2f}): {answer[:80]}")
            return {"answer": answer, "confidence": round(confidence, 2), "quality": quality_score}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            if attempt == MODEL_SERVER_MAX_RETRIES:
                _model_service_unavailable = True
                _model_service_down_until = time.time() + MODEL_SERVER_DOWN_COOLDOWN_SEC
                logger.warning("Model service call failed after retries: %s", exc)
                return None
            sleep_time = MODEL_SERVER_RETRY_BACKOFF_SEC * (2 ** attempt)
            time.sleep(sleep_time)
    return None


def _query_model_server_batch(pairs: List[Dict[str, str]]) -> List[Optional[Dict[str, Any]]]:
    """Call external QA batch endpoint and return aligned answer payloads."""
    global _model_service_unavailable, _model_service_down_until

    if not MODEL_SERVER_ENABLED:
        _model_service_unavailable = True
        return [None for _ in pairs]

    if _model_service_unavailable and time.time() < _model_service_down_until:
        return [None for _ in pairs]

    if not pairs:
        return []

    batch_url = MODEL_SERVER_URL.rsplit("/", 1)[0] + "/qa_batch"
    results: List[Optional[Dict[str, Any]]] = []
    request_batch_size = max(1, MODEL_SERVER_BATCH_SIZE)

    for start in range(0, len(pairs), request_batch_size):
        chunk = pairs[start:start + request_batch_size]
        payload = json.dumps({"requests": chunk}).encode("utf-8")
        request = urllib.request.Request(
            batch_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        chunk_result: Optional[List[Optional[Dict[str, Any]]]] = None
        for attempt in range(MODEL_SERVER_MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(request, timeout=MODEL_SERVER_TIMEOUT_SEC) as response:
                    response_data = json.loads(response.read().decode("utf-8"))

                responses = response_data.get("responses", [])
                parsed: List[Optional[Dict[str, Any]]] = []
                for item in responses:
                    answer = str(item.get("answer", "")).strip()
                    confidence = float(item.get("confidence", -999.0))
                    
                    # PHASE 1: Stricter validation with quality scoring
                    if len(answer) < MIN_ANSWER_LENGTH or confidence < -1.0:
                        parsed.append(None)
                    else:
                        quality_score = _score_answer_quality(answer, confidence)
                        if quality_score < 0.3:
                            parsed.append(None)
                        else:
                            answer = _normalize_answer(answer)
                            parsed.append({"answer": answer, "confidence": round(confidence, 2), "quality": quality_score})

                while len(parsed) < len(chunk):
                    parsed.append(None)
                chunk_result = parsed[:len(chunk)]
                _model_service_unavailable = False
                _model_service_down_until = 0.0
                break
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
                if attempt == MODEL_SERVER_MAX_RETRIES:
                    logger.warning("Model service batch call failed after retries: %s", exc)
                    _model_service_unavailable = True
                    _model_service_down_until = time.time() + MODEL_SERVER_DOWN_COOLDOWN_SEC
                    chunk_result = [None for _ in chunk]
                    results.extend(chunk_result)
                    remaining = len(pairs) - (start + len(chunk))
                    if remaining > 0:
                        results.extend([None for _ in range(remaining)])
                    return results
                else:
                    sleep_time = MODEL_SERVER_RETRY_BACKOFF_SEC * (2 ** attempt)
                    time.sleep(sleep_time)

        results.extend(chunk_result or [None for _ in chunk])

    return results

def _find_answer(question: str, context: str) -> Optional[Dict[str, Any]]:
    """Run one QA inference against the external model service."""
    return _query_model_server(question, context)


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
        if _model_service_unavailable:
            explanation = (
                f"Model service unavailable; fallback applied. This clause is {pct}% similar "
                f"to a known {risk_level} risk \"{top['clause_type']}\" clause in the knowledge base."
            )
        else:
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
    """Analyze a batch of clauses and use QA batch mode when enabled."""
    if not QA_BATCH_MODE_ENABLED:
        return [
            analyze_clause_with_llm(c, r)
            for c, r in zip(contract_clauses, query_results_list)
        ]

    clause_data: List[Dict[str, Any]] = []
    qa_pairs: List[Dict[str, str]] = []
    qa_index_map: List[List[tuple[str, int]]] = []

    for clause_text, retrieved in zip(contract_clauses, query_results_list):
        all_matches = _extract_matches(retrieved)
        similar_clauses = _filter_matches(all_matches)

        indices_for_clause: List[tuple[str, int]] = []
        for level in ["HIGH", "MEDIUM", "LOW"]:
            for question in QUESTIONS[level]:
                pair_index = len(qa_pairs)
                qa_pairs.append({"question": question, "context": clause_text})
                indices_for_clause.append((question, pair_index))

        clause_data.append({
            "clause_text": clause_text,
            "similar_clauses": similar_clauses,
        })
        qa_index_map.append(indices_for_clause)

    qa_results = _query_model_server_batch(qa_pairs)
    analyses: List[Dict[str, Any]] = []

    for idx, metadata in enumerate(clause_data):
        clause_text = metadata["clause_text"]
        similar_clauses = metadata["similar_clauses"]

        highest_level_found: Optional[str] = None
        found_indicators: List[str] = []

        for question, result_index in qa_index_map[idx]:
            res = qa_results[result_index] if result_index < len(qa_results) else None
            if not res:
                continue

            label = QUESTION_LABELS.get(question, question)
            found_indicators.append(label)

            if highest_level_found is None:
                if question in QUESTIONS["HIGH"]:
                    highest_level_found = "HIGH"
                elif question in QUESTIONS["MEDIUM"]:
                    highest_level_found = "MEDIUM"
                else:
                    highest_level_found = "LOW"

        if highest_level_found:
            risk_level = highest_level_found
            indicators_str = ", ".join(found_indicators[:3])
            explanation = f"This clause contains: {indicators_str}."
        elif similar_clauses:
            top = similar_clauses[0]
            sev = top["severity"]
            risk_level = sev if sev in ("HIGH", "MEDIUM", "LOW") else "LOW"
            pct = round(top["score"] * 100, 1)
            if _model_service_unavailable:
                explanation = (
                    f"Model service unavailable; fallback applied. This clause is {pct}% similar "
                    f"to a known {risk_level} risk \"{top['clause_type']}\" clause in the knowledge base."
                )
            else:
                explanation = (
                    f"This clause is {pct}% similar to a known {risk_level} risk "
                    f"\"{top['clause_type']}\" clause in the knowledge base."
                )
        else:
            risk_level = "LOW"
            explanation = "No risk patterns detected. This clause appears to be standard boilerplate."

        analyses.append(
            {
                "clause_text": clause_text,
                "risk_level": risk_level,
                "explanation": explanation,
                "similar_clauses": similar_clauses,
            }
        )

    return analyses

def get_model_service_status() -> Dict[str, Any]:
    """Return model-service connectivity and configuration status."""
    health_url = MODEL_SERVER_URL.rsplit("/", 1)[0] + "/health"
    if not MODEL_SERVER_ENABLED:
        return {"enabled": False, "status": "disabled", "url": health_url}

    request = urllib.request.Request(health_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=min(2.0, MODEL_SERVER_TIMEOUT_SEC)) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        status = str(response_data.get("status", "unknown"))
        normalized = "ready" if status == "ok" else status
        return {"enabled": True, "status": normalized, "url": health_url}
    except Exception:
        return {"enabled": True, "status": "offline", "url": health_url}


def summarize_contract_analysis(analyses: List[Dict[str, Any]]) -> str:
    """
    Generate a summary of the contract analysis results using the local QA model.
    
    Uses stricter confidence threshold (SUMMARY_MIN_CONFIDENCE) for better quality.
    """
    if not analyses:
        return "No clauses were analyzed. Unable to generate summary."
    
    # Build text context from high/medium risk clauses first, fallback to all clauses
    high_med_clauses = [
        a.get("clause_text", "") for a in analyses 
        if a.get("risk_level") in ("HIGH", "MEDIUM")
    ]
    if high_med_clauses:
        context = " ".join(high_med_clauses)
    else:
        context = " ".join([a.get("clause_text", "") for a in analyses])       
        
    question = "What are the critical risks and obligations in this contract?" 
    res = _query_model_server(question, context)

    if res and res.get("answer") and res.get("quality", 0.0) >= SUMMARY_MIN_CONFIDENCE:
        return f"Contract Summary (AI Generated):\n{res['answer']}\n\nNote: This is an extractive summary based on identified HIGH and MEDIUM risk clauses."

    # PHASE 1: Better fallback message instead of generic error
    high_count = len([a for a in analyses if a.get("risk_level") == "HIGH"])
    med_count = len([a for a in analyses if a.get("risk_level") == "MEDIUM"])
    
    if high_count > 0 or med_count > 0:
        return (
            f"**Contract Summary (Structured)**\n\n"
            f"HIGH RISK CLAUSES: {high_count}\n"
            f"MEDIUM RISK CLAUSES: {med_count}\n"
            f"Total clauses analyzed: {len(analyses)}\n\n"
            f"*Note: AI-generated summary quality was low. Please review the detailed analysis results below.*"
        )
    
    return "No significant risks identified in this contract. The AI model found only LOW or UNKNOWN risk clauses."
