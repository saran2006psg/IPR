#!/usr/bin/env python3
"""End-to-end diagnostic for model usage in reasoner and chat orchestration.

Usage:
    python backend/scripts/check_model_integration.py
    python backend/scripts/check_model_integration.py --strict
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict


def _bootstrap_imports() -> None:
    """Make backend package importable and load .env values."""
    backend_dir = Path(__file__).resolve().parent.parent
    repo_root = backend_dir.parent

    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(repo_root / ".env")
    except Exception:
        pass


def _sample_retrieval_result() -> Dict[str, Any]:
    """Synthetic retrieval payload shaped like Pinecone response."""
    return {
        "matches": [
            {
                "score": 0.93,
                "metadata": {
                    "clause_text": "Either party may terminate this Agreement at any time without cause with 30 days written notice.",
                    "severity": "MEDIUM",
                    "clause_type": "termination",
                },
            }
        ]
    }


def main() -> int:
    _bootstrap_imports()

    from chat_orchestrator import answer_contract_question
    from retrieval_pipeline.llm_reasoner import analyze_clause_with_llm, get_model_service_status

    parser = argparse.ArgumentParser(description="Check whether model server is integrated and used by backend paths.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if reasoner/chat fall back instead of model answers")
    args = parser.parse_args()

    print("=" * 72)
    print("MODEL INTEGRATION CHECK")
    print("=" * 72)

    status = get_model_service_status()
    model_state = str(status.get("status", "unknown"))
    print(f"Model service status : {model_state}")
    print(f"Model service URL    : {status.get('url', 'n/a')}")

    if model_state != "ready":
        print("FAIL: model service is not ready. Start model_server.py first.")
        return 2

    clause_text = (
        "Either party may terminate this Agreement at any time without cause "
        "with 30 days written notice."
    )

    print("\n[1/2] Reasoner path diagnostic...")
    reasoner_result = analyze_clause_with_llm(clause_text, _sample_retrieval_result())
    reasoner_model_used = bool(reasoner_result.get("model_used", False))
    reasoner_fallback = bool(reasoner_result.get("fallback_used", False))

    print(f"risk_level      : {reasoner_result.get('risk_level')}")
    print(f"model_used      : {reasoner_model_used}")
    print(f"fallback_used   : {reasoner_fallback}")
    print(f"explanation     : {reasoner_result.get('explanation', '')}")

    print("\n[2/2] Chat orchestration diagnostic...")
    chat_result = answer_contract_question(
        question="Can a party terminate this contract without cause?",
        analyses=[reasoner_result],
        summary="Synthetic summary for diagnostic.",
        chat_history=[],
    )
    chat_fallback = bool(chat_result.get("fallback_used", False))

    print(f"confidence      : {chat_result.get('confidence', 0.0)}")
    print(f"fallback_used   : {chat_fallback}")
    print(f"answer          : {chat_result.get('answer', '')}")

    if args.strict:
        if not reasoner_model_used:
            print("FAIL: strict mode: reasoner did not mark model_used=True.")
            return 3
        if chat_fallback:
            print("FAIL: strict mode: chat path fell back instead of model answer.")
            return 4

    if not reasoner_model_used or chat_fallback:
        print("WARN: Integration is reachable, but at least one path used fallback behavior.")
        print("      Use --strict to enforce no-fallback behavior in CI.")
    else:
        print("PASS: Reasoner and chat paths are both using model answers.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
