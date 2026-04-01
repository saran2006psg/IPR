"""LLM reasoner for role-aware contract risk analysis using Groq."""

import logging
import json
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .agreement_profiles import build_role_review_context
from .config import (
    DEFAULT_CONTEXT_AGREEMENT_TYPE,
    DEFAULT_CONTEXT_USER_TYPE,
    GROQ_API_KEY,
    GROQ_API_URL,
    GROQ_DOWN_COOLDOWN_SEC,
    GROQ_ENABLED,
    GROQ_MAX_RETRIES,
    GROQ_MODEL,
    GROQ_RETRY_BACKOFF_SEC,
    GROQ_TIMEOUT_SEC,
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
        if not isinstance(metadata, dict):
            metadata = {}

        text = metadata.get("clause_text") or metadata.get("text") or ""
        match_id = match.get("id", "") if isinstance(match, dict) else getattr(match, "id", "")
        rule_id = (
            metadata.get("rule_id")
            or metadata.get("kb_id")
            or metadata.get("source_id")
            or metadata.get("clause_id")
            or ""
        )
        rule_name = (
            metadata.get("rule_name")
            or metadata.get("title")
            or metadata.get("name")
            or metadata.get("clause_type")
            or ""
        )
        normalized.append(
            {
                "text": text,
                "severity": str(metadata.get("severity", "unknown")).upper(),
                "clause_type": str(metadata.get("clause_type", "unknown")),
                "score": round(score, 4),
                "match_id": str(match_id or ""),
                "rule_id": str(rule_id or ""),
                "rule_name": str(rule_name or ""),
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
    if any(answer_lower.startswith(conj + " ") for conj in ["and", "or", "but"]):
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
    leading_prefixes = ["and ", "or ", "but "]
    while any(answer.lower().startswith(p) for p in leading_prefixes):
        for prefix in leading_prefixes:
            if answer.lower().startswith(prefix):
                answer = answer[len(prefix):].strip()
                break
    
    # Collapse multiple spaces
    answer = re.sub(r"\s+", " ", answer)
    
    return answer


# ---------------------------------------------------------------------------
# QA inference via Groq
# ---------------------------------------------------------------------------

def _extract_json_block(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse a JSON object from model output text."""
    if not raw_text:
        return None

    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except ValueError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None

    try:
        parsed = json.loads(text[start:end + 1])
        return parsed if isinstance(parsed, dict) else None
    except ValueError:
        return None


def _call_groq_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 400,
) -> Optional[str]:
    """Call Groq chat completions and return assistant message content."""
    global _model_service_unavailable, _model_service_down_until

    if not GROQ_ENABLED or not GROQ_API_KEY:
        _model_service_unavailable = True
        return None

    if _model_service_unavailable and time.time() < _model_service_down_until:
        return None

    payload = json.dumps(
        {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        GROQ_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "python-requests/2.32.3",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        method="POST",
    )

    for attempt in range(GROQ_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=GROQ_TIMEOUT_SEC) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            choices = response_data.get("choices", [])
            if not choices:
                return None

            content = str(choices[0].get("message", {}).get("content", "")).strip()
            _model_service_unavailable = False
            _model_service_down_until = 0.0
            return content or None

        except urllib.error.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = ""

            if attempt == GROQ_MAX_RETRIES:
                _model_service_unavailable = True
                _model_service_down_until = time.time() + GROQ_DOWN_COOLDOWN_SEC
                if error_body:
                    logger.warning(
                        "Groq call failed after retries: HTTP %s body=%s",
                        exc.code,
                        error_body[:500],
                    )
                else:
                    logger.warning("Groq call failed after retries: %s", exc)
                return None

            sleep_time = GROQ_RETRY_BACKOFF_SEC * (2 ** attempt)
            time.sleep(sleep_time)

        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt == GROQ_MAX_RETRIES:
                _model_service_unavailable = True
                _model_service_down_until = time.time() + GROQ_DOWN_COOLDOWN_SEC
                logger.warning("Groq call failed after retries: %s", exc)
                return None
            sleep_time = GROQ_RETRY_BACKOFF_SEC * (2 ** attempt)
            time.sleep(sleep_time)

    return None


def _query_model_server(
    question: str,
    context: str,
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Run context-grounded QA through Groq and return normalized answer payload."""
    role_context = build_role_review_context(
        agreement_type or DEFAULT_CONTEXT_AGREEMENT_TYPE,
        user_type or DEFAULT_CONTEXT_USER_TYPE,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a legal contract assistant. Answer using only the provided context. "
                "If the context is insufficient, state that clearly in one sentence."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{role_context}\n\n"
                f"Question: {question}\n\n"
                f"Context:\n{context}"
            ),
        },
    ]

    answer = _call_groq_chat(messages, temperature=0.05, max_tokens=320)
    if not answer:
        return None

    answer = re.sub(r"\s+", " ", answer).strip()
    if len(answer) < MIN_ANSWER_LENGTH:
        return None

    confidence = 1.2
    quality_score = _score_answer_quality(answer, confidence)
    if quality_score < 0.25:
        return None

    return {
        "answer": answer,
        "confidence": round(confidence, 2),
        "quality": quality_score,
    }


def _query_model_server_batch(
    pairs: List[Dict[str, str]],
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> List[Optional[Dict[str, Any]]]:
    """Compatibility helper that runs Groq QA calls sequentially for each pair."""
    results: List[Optional[Dict[str, Any]]] = []
    for pair in pairs:
        results.append(
            _query_model_server(
                pair.get("question", ""),
                pair.get("context", ""),
                agreement_type=agreement_type,
                user_type=user_type,
            )
        )
    return results


def _find_answer(
    question: str,
    context: str,
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Run one QA inference against Groq."""
    return _query_model_server(
        question,
        context,
        agreement_type=agreement_type,
        user_type=user_type,
    )


def query_model_service(
    question: str,
    context: str,
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Public helper used by other modules to run one QA inference call."""
    return _query_model_server(
        question,
        context,
        agreement_type=agreement_type,
        user_type=user_type,
    )


def _summarize_similar_clauses(similar_clauses: List[Dict[str, Any]], max_items: int = 3) -> str:
    """Build compact similar-clause context for role-aware prompting."""
    lines: List[str] = []
    for idx, clause in enumerate(similar_clauses[:max_items], start=1):
        text = re.sub(r"\s+", " ", str(clause.get("text", ""))).strip()
        if len(text) > 220:
            text = text[:220].rstrip() + "..."
        lines.append(
            f"{idx}. severity={clause.get('severity', 'UNKNOWN')}, "
            f"type={clause.get('clause_type', 'unknown')}, "
            f"similarity={clause.get('score', 0.0)} -> {text}"
        )
    return "\n".join(lines) if lines else "No close rule matches above threshold."


def _analyze_clause_with_groq(
    clause_text: str,
    similar_clauses: List[Dict[str, Any]],
    agreement_type: str,
    user_type: str,
) -> Optional[Dict[str, Any]]:
    """Classify clause risk from the selected user-role perspective."""
    role_context = build_role_review_context(agreement_type, user_type)
    similar_context = _summarize_similar_clauses(similar_clauses)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a legal risk reviewer. Return STRICT JSON only with keys: "
                "risk_level, explanation, indicators, confidence. "
                "risk_level must be one of HIGH, MEDIUM, LOW."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{role_context}\n\n"
                f"Contract clause to review:\n{clause_text}\n\n"
                f"Relevant knowledge-base matches:\n{similar_context}\n\n"
                "Rate risk for this selected user role. "
                "Keep explanation under 80 words and explicitly mention why it is risky for this role."
            ),
        },
    ]

    raw = _call_groq_chat(messages, temperature=0.1, max_tokens=320)
    parsed = _extract_json_block(raw or "")
    if not parsed:
        return None

    risk_level = str(parsed.get("risk_level", "UNKNOWN")).upper()
    if risk_level not in {"HIGH", "MEDIUM", "LOW"}:
        return None

    explanation = str(parsed.get("explanation", "")).strip()
    if not explanation:
        return None

    indicators_raw = parsed.get("indicators", [])
    if isinstance(indicators_raw, list):
        indicators = [str(item).strip() for item in indicators_raw if str(item).strip()]
    else:
        indicators = []

    try:
        confidence = float(parsed.get("confidence", 1.2))
    except (TypeError, ValueError):
        confidence = 1.2

    quality_score = _score_answer_quality(explanation, confidence)
    if quality_score < 0.25:
        return None

    return {
        "risk_level": risk_level,
        "explanation": explanation,
        "indicators": indicators,
        "confidence": round(confidence, 2),
        "quality": quality_score,
    }


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze_clause_with_llm(
    clause_text: str,
    retrieved_clauses: Any,
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a single clause and always return a meaningful risk assessment.

    Returns a dict with keys:
        clause_text, risk_level, explanation, similar_clauses
    """
    selected_agreement_type = agreement_type or DEFAULT_CONTEXT_AGREEMENT_TYPE
    selected_user_type = user_type or DEFAULT_CONTEXT_USER_TYPE

    all_matches = _extract_matches(retrieved_clauses)
    similar_clauses = _filter_matches(all_matches)

    model_used = False
    fallback_used = False

    model_result = _analyze_clause_with_groq(
        clause_text,
        similar_clauses,
        selected_agreement_type,
        selected_user_type,
    )

    if model_result:
        model_used = True
        risk_level = model_result["risk_level"]
        explanation = model_result["explanation"]
        if model_result.get("indicators"):
            indicators = ", ".join(model_result["indicators"][:3])
            explanation = f"{explanation} Key signals: {indicators}."

    elif similar_clauses:
        fallback_used = True
        top = similar_clauses[0]
        sev = top["severity"]
        risk_level = sev if sev in ("HIGH", "MEDIUM", "LOW") else "LOW"
        pct = round(top["score"] * 100, 1)
        if _model_service_unavailable:
            explanation = (
                f"Groq service unavailable; fallback applied. For {selected_user_type} in "
                f"{selected_agreement_type}, this clause is {pct}% similar to a known "
                f"{risk_level} risk \"{top['clause_type']}\" clause in the knowledge base."
            )
        else:
            explanation = (
                f"For {selected_user_type} in {selected_agreement_type}, this clause is {pct}% "
                f"similar to a known {risk_level} risk \"{top['clause_type']}\" clause in the knowledge base."
            )
    else:
        fallback_used = True
        risk_level = "LOW"
        explanation = (
            f"No role-specific risk patterns detected for {selected_user_type} under "
            f"{selected_agreement_type}."
        )

    return {
        "clause_text": clause_text,
        "risk_level": risk_level,
        "explanation": explanation,
        "model_used": model_used,
        "fallback_used": fallback_used,
        "similar_clauses": similar_clauses,
        "agreement_type": selected_agreement_type,
        "user_type": selected_user_type,
    }


def analyze_clauses_with_llm_batch(
    contract_clauses: List[str],
    query_results_list: List[Any],
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Analyze a batch of clauses with role-aware Groq reasoning."""
    return [
        analyze_clause_with_llm(
            clause_text,
            retrieved,
            agreement_type=agreement_type,
            user_type=user_type,
        )
        for clause_text, retrieved in zip(contract_clauses, query_results_list)
    ]

def get_model_service_status() -> Dict[str, Any]:
    """Return Groq connectivity and configuration status."""
    if not GROQ_ENABLED:
        return {
            "enabled": False,
            "status": "disabled",
            "url": GROQ_API_URL,
            "provider": "groq",
            "model": GROQ_MODEL,
        }

    if not GROQ_API_KEY:
        return {
            "enabled": False,
            "status": "missing-api-key",
            "url": GROQ_API_URL,
            "provider": "groq",
            "model": GROQ_MODEL,
        }

    degraded = _model_service_unavailable and time.time() < _model_service_down_until
    return {
        "enabled": True,
        "status": "degraded" if degraded else "ready",
        "url": GROQ_API_URL,
        "provider": "groq",
        "model": GROQ_MODEL,
    }


def summarize_contract_analysis(analyses: List[Dict[str, Any]]) -> str:
    """
    Generate a summary of contract analysis using Groq.
    
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
        
    agreement_type = str(
        analyses[0].get("agreement_type", DEFAULT_CONTEXT_AGREEMENT_TYPE)
    ) if analyses else DEFAULT_CONTEXT_AGREEMENT_TYPE
    user_type = str(
        analyses[0].get("user_type", DEFAULT_CONTEXT_USER_TYPE)
    ) if analyses else DEFAULT_CONTEXT_USER_TYPE

    question = "What are the critical risks and obligations in this contract?"
    res = _query_model_server(
        question,
        context,
        agreement_type=agreement_type,
        user_type=user_type,
    )

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
