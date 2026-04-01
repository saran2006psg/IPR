"""Chat orchestration for contract-grounded QA using the shared model-service endpoint."""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from retrieval_pipeline.config import (
    CHAT_CONTEXT_CLAUSES,
    CHAT_MAX_ANSWER_CHARS,
    CHAT_MIN_CONFIDENCE,
)
from retrieval_pipeline.llm_reasoner import (
    get_model_service_status,
    query_model_service,
    summarize_contract_analysis,
)


_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")
_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "for", "on", "at", "with", "by",
    "is", "are", "was", "were", "be", "been", "being", "this", "that", "these", "those",
    "it", "its", "as", "from", "about", "into", "than", "then", "if", "but", "not",
}

_CLAUSE_REFERENCE_PHRASES = {
    "this clause",
    "that clause",
    "this section",
    "that section",
    "this provision",
    "that provision",
}

_RISK_DISTRIBUTION_HINTS = {
    "risk distribution",
    "distribution",
    "breakdown",
    "how many",
    "count",
    "counts",
    "percentage",
    "percent",
    "%",
    "stats",
    "statistics",
}

_RISK_REASON_HINTS = {
    "why",
    "risky",
    "risky?",
    "high risk",
    "risky contract",
    "why risk",
    "what makes",
    "reason",
    "reasons",
}


def _normalize(text: str) -> str:
    """Normalize text whitespace."""
    return re.sub(r"\s+", " ", text or "").strip()


def _truncate_text_safely(text: str, max_chars: int) -> str:
    """Trim text to a hard cap while preferring sentence/word boundaries."""
    if not isinstance(text, str):
        text = str(text or "")
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text

    cutoff = -1

    sentence_breaks = [
        text.rfind(". ", 0, max_chars),
        text.rfind("! ", 0, max_chars),
        text.rfind("? ", 0, max_chars),
        text.rfind(".\n", 0, max_chars),
        text.rfind("!\n", 0, max_chars),
        text.rfind("?\n", 0, max_chars),
    ]
    cutoff = max(sentence_breaks)

    if cutoff < int(max_chars * 0.65):
        cutoff = text.rfind("\n", 0, max_chars)
    if cutoff < int(max_chars * 0.65):
        cutoff = text.rfind(" ", 0, max_chars)
    if cutoff <= 0:
        cutoff = max(1, max_chars - 3)

    trimmed = text[:cutoff].rstrip(" .!?,;:\n")
    if not trimmed:
        trimmed = text[: max(1, max_chars - 3)].rstrip()
    return trimmed + "..."


def _normalize_token(token: str) -> str:
    """Lightweight token normalization for overlap scoring."""
    w = token.lower().strip()
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _tokenize_keywords(text: str) -> List[str]:
    """Extract keywords from text."""
    keywords: List[str] = []
    for raw in _WORD_RE.findall(text):
        norm = _normalize_token(raw)
        if len(norm) > 2 and norm not in _STOPWORDS:
            keywords.append(norm)
    return keywords


def build_summary(analyses: List[Dict[str, Any]]) -> str:
    """Build contract summary string for chat grounding."""
    return summarize_contract_analysis(analyses)


def _safe_clause_index(index: Any, total: int) -> Optional[int]:
    """Return validated clause index when available."""
    if not isinstance(index, int):
        return None
    if 0 <= index < total:
        return index
    return None


def _get_recent_clause_index(chat_history: List[Dict[str, Any]], total_clauses: int) -> Optional[int]:
    """Infer most recent clause index from assistant citations in chat history."""
    for msg in reversed(chat_history or []):
        if msg.get("role") != "assistant":
            continue

        citations = msg.get("citations") or []
        if not citations:
            continue

        for citation in citations:
            raw_idx = citation.get("clause_index")
            if isinstance(raw_idx, int):
                idx = _safe_clause_index(raw_idx, total_clauses)
                if idx is not None:
                    return idx
            elif isinstance(raw_idx, str) and raw_idx.isdigit():
                idx = _safe_clause_index(int(raw_idx), total_clauses)
                if idx is not None:
                    return idx
    return None


def _is_clause_specific_question(question: str) -> bool:
    """Detect user phrasing that refers to a currently selected clause."""
    q = question.lower()
    if any(phrase in q for phrase in _CLAUSE_REFERENCE_PHRASES):
        return True
    if re.search(r"\bclause\s+\d+\b", q):
        return True
    if "clause" in q and "clauses" not in q and "contract" not in q:
        if any(token in q for token in ["why", "explain", "what", "how"]):
            return True
    return q.startswith("explain this") or q.startswith("what's wrong with this") or q.startswith("whats wrong with this")


def _format_similarity_pct(score: Any) -> str:
    """Format similarity score as a percentage string."""
    try:
        return f"{float(score) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _best_rule_label(match: Dict[str, Any]) -> str:
    """Pick the most descriptive rule label from match metadata."""
    rule_name = _normalize(str(match.get("rule_name", "")))
    clause_type = _normalize(str(match.get("clause_type", "")))
    if rule_name and rule_name.lower() not in {"unknown", "n/a", "none"}:
        return rule_name
    if clause_type and clause_type.lower() not in {"unknown", "n/a", "none"}:
        return clause_type
    return "unknown-rule"


def _build_db_match_section(similar_clauses: List[Dict[str, Any]], max_rules: int = 1) -> str:
    """Build user-friendly database match details for clause explanations."""
    if not similar_clauses:
        return ""

    lines = ["Matched rule(s) from DB:"]
    for rank, match in enumerate(similar_clauses[:max_rules], start=1):
        severity = str(match.get("severity", "UNKNOWN")).upper()
        label = _best_rule_label(match)
        similarity = _format_similarity_pct(match.get("score", 0.0))

        match_id = _normalize(str(match.get("match_id") or match.get("rule_id") or ""))
        id_part = f" [{match_id}]" if match_id else ""
        lines.append(f"{rank}. {severity} - {label}{id_part} ({similarity} match)")

        reference_text = _normalize(str(match.get("text", "")))
        if reference_text:
            lines.append(f"   Reference: \"{_summarize_clause_label(reference_text, max_len=80)}\"")

    return "\n".join(lines)


def _build_clause_explanation_answer(clause_analysis: Dict[str, Any]) -> str:
    """Create a readable answer from analyzed clause metadata."""
    clause_text = _normalize(clause_analysis.get("clause_text", ""))
    explanation = _normalize(clause_analysis.get("explanation", ""))
    risk = str(clause_analysis.get("risk_level", "LOW")).upper()

    if len(clause_text) > 180:
        clause_text = clause_text[:180].rstrip() + "..."

    pieces = [f"In simple terms, this clause says: {clause_text}"]

    if risk in {"HIGH", "MEDIUM"}:
        if explanation:
            pieces.append(f"Why this is risky: {explanation}")
        else:
            pieces.append("Why this is risky: This clause matches known elevated-risk patterns.")
    elif explanation:
        pieces.append(f"Why this is not risky: {explanation}")

    db_match_section = ""
    similar_clauses = clause_analysis.get("similar_clauses", [])
    if isinstance(similar_clauses, list):
        db_match_section = _build_db_match_section(similar_clauses)

    if db_match_section:
        pieces.append(db_match_section)
    elif risk in {"HIGH", "MEDIUM"}:
        pieces.append("Matched rule(s) from DB: No similarity rule above threshold for this clause.")

    pieces.append(f"Risk level: {risk}.")

    answer = "\n\n".join(pieces)
    if len(answer) <= CHAT_MAX_ANSWER_CHARS:
        return answer

    # Keep "why risky" and matched DB rule details even when answer must be shortened.
    if len(pieces) >= 2:
        tail_sections = pieces[1:]
        tail_text = "\n\n".join(tail_sections)
        remaining = max(40, CHAT_MAX_ANSWER_CHARS - len(tail_text) - 2)
        lead = pieces[0]
        if len(lead) > remaining:
            lead = lead[: max(0, remaining - 3)].rstrip() + "..."
        answer = "\n\n".join([lead] + tail_sections)

    if len(answer) > CHAT_MAX_ANSWER_CHARS:
        answer = _truncate_text_safely(answer, CHAT_MAX_ANSWER_CHARS)
    return answer


def _severity_rank(level: str) -> int:
    """Sort helper for risk severity ordering."""
    normalized = str(level or "").upper()
    if normalized == "HIGH":
        return 3
    if normalized == "MEDIUM":
        return 2
    if normalized == "LOW":
        return 1
    return 0


def _summarize_clause_label(clause_text: str, max_len: int = 95) -> str:
    """Create compact clause snippet label for user-facing summaries."""
    normalized = _normalize(clause_text)
    if len(normalized) <= max_len:
        return normalized
    return normalized[:max_len].rstrip() + "..."


def _build_risk_reason_answer(analyses: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """Build a contract-level explanation of why the contract is risky."""
    stats = _get_risk_stats(analyses)
    total = max(1, len(analyses))

    ranked: List[Tuple[int, Dict[str, Any]]] = []
    for idx, clause in enumerate(analyses):
        ranked.append((idx, clause))

    ranked.sort(
        key=lambda item: (
            _severity_rank(str(item[1].get("risk_level", "LOW"))),
            len(_normalize(item[1].get("explanation", ""))),
        ),
        reverse=True,
    )
    top = ranked[:3]

    if stats["HIGH"] == 0 and stats["MEDIUM"] == 0:
        answer = (
            f"This contract does not appear highly risky overall. "
            f"Out of {total} clauses, {stats['LOW']} are LOW risk and none are HIGH/MEDIUM."
        )
        return answer, []

    lines = [
        (
            f"This contract is marked risky because {stats['HIGH']} of {total} clauses are HIGH risk "
            f"and {stats['MEDIUM']} are MEDIUM risk."
        ),
        "Main risk drivers:",
    ]

    citations: List[Dict[str, Any]] = []
    for clause_index, clause in top:
        level = str(clause.get("risk_level", "LOW")).upper()
        if level not in {"HIGH", "MEDIUM"}:
            continue

        explanation = _normalize(clause.get("explanation", ""))
        snippet = _summarize_clause_label(clause.get("clause_text", ""))
        reason = explanation or "Potential legal exposure based on similarity and model signals."
        lines.append(f"- Clause {clause_index + 1} ({level}): {reason} (\"{snippet}\")")

        citations.append(
            {
                "clause_index": clause_index,
                "risk_level": level,
                "relevance_score": 1.0,
                "snippet": clause.get("clause_text", ""),
            }
        )

    if len(lines) == 2:
        lines.append("- High/medium risk was detected, but detailed risk reasons were not available.")

    return "\n".join(lines), citations


def _build_contract_summary_answer(
    analyses: List[Dict[str, Any]],
    fallback_summary: str,
    max_chars: int = CHAT_MAX_ANSWER_CHARS,
) -> str:
    """Build stable contract summary from analysis metadata."""
    stats = _get_risk_stats(analyses)
    total = len(analyses)
    total_safe = max(1, total)

    ranked: List[Tuple[int, Dict[str, Any]]] = []
    for idx, clause in enumerate(analyses):
        ranked.append((idx, clause))

    ranked.sort(
        key=lambda item: (
            _severity_rank(str(item[1].get("risk_level", "LOW"))),
            len(_normalize(item[1].get("explanation", ""))),
        ),
        reverse=True,
    )

    lines: List[str] = [
        (
            f"Contract contains {total} analyzed clauses: "
            f"{stats['HIGH']} HIGH risk, {stats['MEDIUM']} MEDIUM risk, {stats['LOW']} LOW risk."
        )
    ]

    if stats["HIGH"] > 0:
        lines.append("Overall assessment: elevated legal risk requiring review before signature.")
    elif stats["MEDIUM"] > 0:
        lines.append("Overall assessment: moderate risk with clauses needing clarification.")
    else:
        lines.append("Overall assessment: mostly standard terms with low risk exposure.")

    key_points_added = 0
    for idx, clause in ranked:
        level = str(clause.get("risk_level", "LOW")).upper()
        if level not in {"HIGH", "MEDIUM"}:
            continue
        explanation = _normalize(clause.get("explanation", ""))
        if not explanation:
            continue
        explanation_brief = _summarize_clause_label(explanation, max_len=110)
        next_line = f"Key clause {idx + 1} ({level}): {explanation_brief}"
        candidate = "\n".join(lines + [next_line])
        if len(candidate) > max_chars:
            break
        lines.append(next_line)
        key_points_added += 1
        if key_points_added >= 3:
            break

    if key_points_added == 0:
        if fallback_summary:
            fallback_line = _truncate_text_safely(_normalize(fallback_summary), min(350, max_chars))
            lines.append(fallback_line)
        else:
            fallback_line = (
                f"Risk distribution snapshot: HIGH {stats['HIGH']*100//total_safe}%, "
                f"MEDIUM {stats['MEDIUM']*100//total_safe}%, LOW {stats['LOW']*100//total_safe}%."
            )
            lines.append(fallback_line)

    answer = "\n".join(lines)
    if len(answer) > max_chars:
        answer = _truncate_text_safely(answer, max_chars)
    return answer


def _get_top_relevant_clauses(
    question: str,
    analyses: List[Dict[str, Any]],
    top_k: int = CHAT_CONTEXT_CLAUSES,
    preferred_clause_index: Optional[int] = None,
) -> List[Tuple[int, Dict[str, Any]]]:
    """Rank clauses by keyword overlap with question."""
    q_tokens = set(_tokenize_keywords(question))
    if not q_tokens:
        if preferred_clause_index is not None:
            return [(preferred_clause_index, analyses[preferred_clause_index])]
        return []
    
    scored: List[Tuple[float, int, int, Dict[str, Any]]] = []
    for idx, analysis in enumerate(analyses):
        clause_text = analysis.get("clause_text", "")
        explanation = analysis.get("explanation", "")
        combined_text = f"{clause_text} {explanation}"
        clause_tokens = set(_tokenize_keywords(combined_text))
        
        overlap = len(q_tokens & clause_tokens)
        coverage = overlap / max(1, len(q_tokens))
        risk_boost = {
            "HIGH": 0.15,
            "MEDIUM": 0.08,
            "LOW": 0.0,
        }.get(str(analysis.get("risk_level", "LOW")).upper(), 0.0)

        selected_boost = 0.35 if preferred_clause_index is not None and idx == preferred_clause_index else 0.0
        score = (overlap * 3.0) + (coverage * 2.0) + risk_boost + selected_boost
        
        scored.append((score, overlap, idx, analysis))

    if scored and max(item[1] for item in scored) == 0:
        if preferred_clause_index is not None:
            return [(preferred_clause_index, analyses[preferred_clause_index])]
        return []
    
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [(idx, analysis) for _, _, idx, analysis in scored[:top_k]]


def _run_roberta_qa(
    question: str,
    context: str,
    max_answer_length: int = 500,
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Run QA using the shared Groq endpoint used by risk analysis."""
    result = query_model_service(
        question,
        context,
        agreement_type=agreement_type,
        user_type=user_type,
    )
    if not result:
        status = get_model_service_status().get("status", "unknown")
        logger.warning("Model service not available for chat QA (status=%s)", status)
        return {
            "answer": "",
            "confidence": 0.0,
            "quality": 0.0,
        }

    answer = str(result.get("answer", "")).strip()
    if len(answer) > max_answer_length:
        answer = _truncate_text_safely(answer, max_answer_length)

    return {
        "answer": answer,
        "confidence": float(result.get("confidence", 0.0)),
        "quality": float(result.get("quality", 0.0)),
    }


def _is_summary_question(question: str) -> bool:
    """Check if question is asking for overall summary."""
    q = question.lower()
    return any(k in q for k in ["summary", "summarize", "overall", "report", "overview"])


def _is_risk_distribution_question(question: str) -> bool:
    """Check if question is asking about risk distribution."""
    q = question.lower()
    if "risk" not in q and "high" not in q and "medium" not in q and "low" not in q:
        return False
    return any(hint in q for hint in _RISK_DISTRIBUTION_HINTS)


def _is_risk_reason_question(question: str) -> bool:
    """Check if user asks why contract/clause is risky."""
    q = question.lower()
    if "risk" not in q and "risky" not in q:
        return False
    return any(hint in q for hint in _RISK_REASON_HINTS)


def _get_risk_stats(analyses: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get risk level distribution."""
    stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for item in analyses:
        level = str(item.get("risk_level", "UNKNOWN")).upper()
        stats[level] = stats.get(level, 0) + 1
    return stats


def answer_contract_question(
    question: str,
    analyses: List[Dict[str, Any]],
    summary: str,
    chat_history: List[Dict[str, Any]],
    selected_clause_index: Optional[int] = None,
    agreement_type: Optional[str] = None,
    user_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate grounded answer using the shared model-service QA endpoint.
    
    Process:
    1. Handle special cases (summary/distribution questions)
    2. Resolve clause context (selected/recent)
    3. Get top relevant clauses
    3. Run model-service QA on each clause
    4. Return best answer with citations
    """
    total_clauses = len(analyses)
    selected_idx = _safe_clause_index(selected_clause_index, total_clauses)
    clause_specific_question = _is_clause_specific_question(question)

    if selected_idx is None and clause_specific_question:
        selected_idx = _get_recent_clause_index(chat_history, total_clauses)
    
    # Handle summary questions
    if _is_summary_question(question):
        answer = _build_contract_summary_answer(
            analyses,
            summary,
            max_chars=CHAT_MAX_ANSWER_CHARS,
        )
        return {
            "answer": answer,
            "confidence": 1.0,
            "fallback_used": False,
            "citations": [
                {
                    "clause_index": i,
                    "risk_level": a.get("risk_level", "LOW"),
                    "relevance_score": 1.0,
                    "snippet": a.get("clause_text", "")
                }
                for i, a in enumerate(analyses[:5])
            ],
        }

    if clause_specific_question:
        if selected_idx is None:
            return {
                "answer": (
                    "Please select a clause first, or ask with a specific topic like "
                    "'Explain clause 4 termination notice'."
                ),
                "confidence": 0.0,
                "fallback_used": True,
                "citations": [],
            }

        selected_clause = analyses[selected_idx]
        return {
            "answer": _truncate_text_safely(
                _build_clause_explanation_answer(selected_clause),
                CHAT_MAX_ANSWER_CHARS,
            ),
            "confidence": 0.96,
            "fallback_used": False,
            "citations": [
                {
                    "clause_index": selected_idx,
                    "risk_level": selected_clause.get("risk_level", "LOW"),
                    "relevance_score": 1.0,
                    "snippet": selected_clause.get("clause_text", ""),
                }
            ],
            "primary_clause_index": selected_idx,
        }
    
    # Handle risk distribution questions
    if _is_risk_distribution_question(question):
        stats = _get_risk_stats(analyses)
        total = len(analyses)
        answer = (
            f"Risk distribution: {stats['HIGH']} HIGH ({stats['HIGH']*100//total}%), "
            f"{stats['MEDIUM']} MEDIUM ({stats['MEDIUM']*100//total}%), "
            f"{stats['LOW']} LOW ({stats['LOW']*100//total}%)"
        )
        return {
            "answer": answer,
            "confidence": 1.0,
            "fallback_used": False,
            "citations": [],
        }

    if _is_risk_reason_question(question):
        answer, citations = _build_risk_reason_answer(analyses)
        return {
            "answer": _truncate_text_safely(answer, CHAT_MAX_ANSWER_CHARS),
            "confidence": 0.92,
            "fallback_used": False,
            "citations": citations,
        }
    
    relevant = _get_top_relevant_clauses(
        question,
        analyses,
        top_k=CHAT_CONTEXT_CLAUSES,
        preferred_clause_index=selected_idx,
    )
    if not relevant:
        return {
            "answer": (
                "I couldn't map this question to a specific clause. "
                "Try mentioning a topic like governing law, termination, liability, payment, or confidentiality."
            ),
            "confidence": 0.0,
            "fallback_used": True,
            "citations": [],
        }
    
    # Run role-aware QA on each clause
    best_answer = ""
    best_confidence = 0.0
    best_clause_idx = -1
    fallback_used = False
    
    for clause_idx, clause_analysis in relevant:
        clause_text = clause_analysis.get("clause_text", "")
        explanation = clause_analysis.get("explanation", "")
        
        # Build context: clause text + explanation + similar clauses
        context_parts = [clause_text]
        if explanation:
            context_parts.append(f"Risk details: {explanation}")
        
        similar = clause_analysis.get("similar_clauses", [])[:2]
        for sim in similar:
            sim_text = sim.get("text", "")
            if sim_text:
                context_parts.append(sim_text[:300])
        
        context = " ".join(context_parts)
        
        # Run QA
        result = _run_roberta_qa(
            question,
            context,
            max_answer_length=CHAT_MAX_ANSWER_CHARS,
            agreement_type=agreement_type,
            user_type=user_type,
        )
        confidence = result.get("confidence", 0.0)
        answer = result.get("answer", "")
        
        # Update best if better
        if confidence > best_confidence and answer.strip():
            best_confidence = confidence
            best_answer = answer.strip()
            best_clause_idx = clause_idx
    
    # Fallback if no answer found
    if not best_answer or best_confidence < CHAT_MIN_CONFIDENCE:
        top_clause = relevant[0][1] if relevant else None
        if top_clause:
            best_answer = _truncate_text_safely(
                _build_clause_explanation_answer(top_clause),
                CHAT_MAX_ANSWER_CHARS,
            )
            best_confidence = max(best_confidence, 0.5)
            best_clause_idx = relevant[0][0]
            fallback_used = True
        else:
            return {
                "answer": "Unable to extract answer from contract clauses.",
                "confidence": 0.0,
                "fallback_used": True,
                "citations": [],
            }
    
    # Build citations
    citations = [
        {
            "clause_index": idx,
            "risk_level": clause.get("risk_level", "LOW"),
            "relevance_score": 1.0,
            "snippet": clause.get("clause_text", ""),
        }
        for idx, clause in relevant
    ]
    
    return {
        "answer": best_answer,
        "confidence": round(best_confidence, 2),
        "fallback_used": fallback_used,
        "citations": citations,
        "primary_clause_index": best_clause_idx,
    }
