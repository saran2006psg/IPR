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

            if len(answer) < 2 or confidence < -5.0:
                return None
            return {"answer": answer, "confidence": round(confidence, 2)}
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
                    if len(answer) < 2 or confidence < -5.0:
                        parsed.append(None)
                    else:
                        parsed.append({"answer": answer, "confidence": round(confidence, 2)})

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
    
    def _clause_preview(text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        cleaned = re.sub(r"^\d+[.)\-:\s]+", "", cleaned)
        return cleaned[:100] + ("..." if len(cleaned) > 100 else "")

    # Count risk levels
    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    high_risk_clauses = []
    medium_risk_clauses = []
    
    for analysis in analyses:
        risk_level = analysis.get("risk_level", "UNKNOWN")
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        if risk_level == "HIGH":
            high_risk_clauses.append(_clause_preview(analysis.get("clause_text", "")))
        elif risk_level == "MEDIUM":
            medium_risk_clauses.append(_clause_preview(analysis.get("clause_text", "")))
    
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
