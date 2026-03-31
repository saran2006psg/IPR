"""Chat orchestration for contract-grounded question answering using local RoBERTa QA model."""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

logger = logging.getLogger(__name__)

from retrieval_pipeline.config import (
    CHAT_CONTEXT_CLAUSES,
    CHAT_HISTORY_TURNS,
    CHAT_MAX_ANSWER_CHARS,
    CHAT_MIN_CONFIDENCE,
    HF_MODEL_PATH,
    HF_MAX_LENGTH,
)
from retrieval_pipeline.llm_reasoner import summarize_contract_analysis

# ============================================================================
# RoBERTa Model Initialization (Singleton)
# ============================================================================

_tokenizer: Optional[AutoTokenizer] = None
_model: Optional[AutoModelForQuestionAnswering] = None
_device: Optional[torch.device] = None


def _load_roberta_model() -> Tuple[Optional[AutoTokenizer], Optional[AutoModelForQuestionAnswering], Optional[torch.device]]:
    """Load local RoBERTa QA model (singleton pattern)."""
    global _tokenizer, _model, _device
    
    if _model is not None:
        return _tokenizer, _model, _device
    
    try:
        logger.info(f"Loading RoBERTa model from: {HF_MODEL_PATH}")
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {_device}")
        
        _tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_PATH, local_files_only=False)
        _model = AutoModelForQuestionAnswering.from_pretrained(HF_MODEL_PATH, local_files_only=False)
        _model.to(_device)
        _model.eval()
        
        logger.info("RoBERTa model loaded successfully")
        return _tokenizer, _model, _device
    except Exception as e:
        logger.error(f"Failed to load RoBERTa model: {e}")
        return None, None, None


_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")
_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "for", "on", "at", "with", "by",
    "is", "are", "was", "were", "be", "been", "being", "this", "that", "these", "those",
    "it", "its", "as", "from", "about", "into", "than", "then", "if", "but", "not",
}


def _normalize(text: str) -> str:
    """Normalize text whitespace."""
    return re.sub(r"\s+", " ", text or "").strip()


def _tokenize_keywords(text: str) -> List[str]:
    """Extract keywords from text."""
    return [
        w.lower()
        for w in _WORD_RE.findall(text)
        if len(w) > 2 and w.lower() not in _STOPWORDS
    ]


def build_summary(analyses: List[Dict[str, Any]]) -> str:
    """Build contract summary string for chat grounding."""
    return summarize_contract_analysis(analyses)


def _get_top_relevant_clauses(
    question: str,
    analyses: List[Dict[str, Any]],
    top_k: int = CHAT_CONTEXT_CLAUSES,
) -> List[Tuple[int, Dict[str, Any]]]:
    """Rank clauses by keyword overlap with question."""
    q_tokens = set(_tokenize_keywords(question))
    if not q_tokens:
        return [(i, a) for i, a in enumerate(analyses[:top_k])]
    
    scored = []
    for idx, analysis in enumerate(analyses):
        clause_text = analysis.get("clause_text", "")
        clause_tokens = set(_tokenize_keywords(clause_text))
        
        # Score based on token overlap and risk level
        overlap = len(q_tokens & clause_tokens)
        risk_boost = {"HIGH": 3, "MEDIUM": 1, "LOW": 0}.get(analysis.get("risk_level", "LOW"), 0)
        score = overlap + risk_boost
        
        scored.append((score, idx, analysis))
    
    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(idx, analysis) for _, idx, analysis in scored[:top_k]]


def _run_roberta_qa(
    question: str,
    context: str,
    max_answer_length: int = 100,
) -> Dict[str, Any]:
    """Run RoBERTa QA model on question + context."""
    tokenizer, model, device = _load_roberta_model()
    
    if model is None or tokenizer is None or device is None:
        logger.warning("RoBERTa model not available, returning empty answer")
        return {
            "answer": "",
            "confidence": 0.0,
            "start_logit": 0.0,
            "end_logit": 0.0,
        }
    
    try:
        # Tokenize inputs
        inputs = tokenizer(
            question,
            context,
            max_length=HF_MAX_LENGTH,
            truncation=True,
            return_tensors="pt",
            padding=True,
        ).to(device)
        
        # Get model predictions
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Extract answer span
        start_logits = outputs.start_logits[0]
        end_logits = outputs.end_logits[0]
        
        start_idx = torch.argmax(start_logits)
        end_idx = torch.argmax(end_logits) + 1
        
        start_logit_val = float(start_logits[start_idx])
        end_logit_val = float(end_logits[end_idx - 1])
        confidence = (start_logit_val + end_logit_val) / 2
        
        # Decode answer
        answer_tokens = inputs.input_ids[0, start_idx:end_idx]
        answer = tokenizer.decode(answer_tokens, skip_special_tokens=True)
        
        # Cap answer length
        if len(answer) > max_answer_length:
            answer = answer[:max_answer_length].rsplit(" ", 1)[0] + "..."
        
        return {
            "answer": answer,
            "confidence": float(torch.sigmoid(torch.tensor(confidence)).item()),
            "start_logit": start_logit_val,
            "end_logit": end_logit_val,
        }
    
    except Exception as e:
        logger.error(f"RoBERTa QA error: {e}")
        return {
            "answer": "",
            "confidence": 0.0,
            "start_logit": 0.0,
            "end_logit": 0.0,
        }


def _is_summary_question(question: str) -> bool:
    """Check if question is asking for overall summary."""
    q = question.lower()
    return any(k in q for k in ["summary", "summarize", "overall", "report", "overview"])


def _is_risk_distribution_question(question: str) -> bool:
    """Check if question is asking about risk distribution."""
    q = question.lower()
    return any(k in q for k in ["risk", "distribution", "how many", "high risk", "medium risk", "low risk"])


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
) -> Dict[str, Any]:
    """
    Generate grounded answer using local RoBERTa QA model.
    
    Process:
    1. Handle special cases (summary/distribution questions)
    2. Get top relevant clauses
    3. Run RoBERTa QA on each clause
    4. Return best answer with citations
    """
    
    # Handle summary questions
    if _is_summary_question(question):
        stats = _get_risk_stats(analyses)
        total = len(analyses)
        answer = (
            f"Contract contains {total} analyzed clauses: "
            f"{stats['HIGH']} HIGH risk, {stats['MEDIUM']} MEDIUM risk, {stats['LOW']} LOW risk.\n\n"
            f"{summary[:CHAT_MAX_ANSWER_CHARS]}"
        )
        return {
            "answer": answer,
            "confidence": 1.0,
            "citations": [
                {
                    "clause_index": i,
                    "risk_level": a.get("risk_level", "LOW"),
                    "relevance_score": 1.0,
                    "snippet": a.get("clause_text", "")[:200] + "..."
                }
                for i, a in enumerate(analyses[:5])
            ],
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
            "citations": [],
        }
    
    # Get relevant clauses
    relevant = _get_top_relevant_clauses(question, analyses, top_k=CHAT_CONTEXT_CLAUSES)
    if not relevant:
        return {
            "answer": "No relevant clauses found in contract.",
            "confidence": 0.0,
            "citations": [],
        }
    
    # Run RoBERTa QA on each clause
    best_answer = ""
    best_confidence = 0.0
    best_clause_idx = -1
    best_clause_info = None
    
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
        
        context = " ".join(context_parts)[:2000]
        
        # Run QA
        result = _run_roberta_qa(question, context)
        confidence = result.get("confidence", 0.0)
        answer = result.get("answer", "")
        
        # Update best if better
        if confidence > best_confidence and answer.strip():
            best_confidence = confidence
            best_answer = answer.strip()
            best_clause_idx = clause_idx
            best_clause_info = clause_analysis
    
    # Fallback if no answer found
    if not best_answer or best_confidence < CHAT_MIN_CONFIDENCE:
        top_clause = relevant[0][1] if relevant else None
        if top_clause:
            best_answer = f"Relevant clause found: {top_clause.get('clause_text', '')[:200]}..."
            best_confidence = 0.5
            best_clause_idx = relevant[0][0]
            best_clause_info = top_clause
        else:
            return {
                "answer": "Unable to extract answer from contract clauses.",
                "confidence": 0.0,
                "citations": [],
            }
    
    # Cap answer length
    if len(best_answer) > CHAT_MAX_ANSWER_CHARS:
        best_answer = best_answer[:CHAT_MAX_ANSWER_CHARS].rsplit(" ", 1)[0] + "..."
    
    # Build citations
    citations = [
        {
            "clause_index": idx,
            "risk_level": clause.get("risk_level", "LOW"),
            "relevance_score": 1.0,
            "snippet": clause.get("clause_text", "")[:220] + ("..." if len(clause.get("clause_text", "")) > 220 else ""),
        }
        for idx, clause in relevant
    ]
    
    return {
        "answer": best_answer,
        "confidence": round(best_confidence, 2),
        "citations": citations,
        "primary_clause_index": best_clause_idx,
    }
