#!/usr/bin/env python3
"""
Contract Risk Analyzer — Simple CLI
Usage:
    python analyze.py <contract.pdf>
    python analyze.py sample_employment_contract.pdf
"""

import sys, os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

RISK_ICON  = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
RISK_LABEL = {"HIGH": "HIGH RISK", "MEDIUM": "MEDIUM RISK", "LOW": "LOW RISK"}

def main():
    if len(sys.argv) < 2:
        print("\nUsage: python analyze.py <contract.pdf>\n")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"\n❌ File not found: {pdf_path}\n")
        sys.exit(1)

    # ── imports ──────────────────────────────────────────────────────────────
    try:
        from ..retrieval_pipeline.config import setup_logging
        from ..retrieval_pipeline.pdf_extractor import extract_pdf_text, validate_pdf
        from ..retrieval_pipeline.clause_segmenter import segment_clauses
        from ..retrieval_pipeline.embedder import embed_clauses
        from ..retrieval_pipeline.retriever import query_pinecone_batch
        from ..retrieval_pipeline.risk_analyzer import analyze_risk_batch, get_risk_summary
        import logging
        setup_logging()
        logging.getLogger().setLevel(logging.WARNING)
    except ImportError as e:
        print(f"❌ Import error: {e}\nRun: pip install -r requirements.txt")
        sys.exit(1)

    # ── pipeline ─────────────────────────────────────────────────────────────
    print(f"\nAnalyzing: {os.path.basename(pdf_path)} …", end="\n\n", flush=True)

    try:
        validate_pdf(pdf_path)
        text    = extract_pdf_text(pdf_path)
        clauses = segment_clauses(text)
        if not clauses:
            print("❌ No clauses found in this PDF.\n"); sys.exit(1)
        vectors  = embed_clauses(clauses)
        qresults = query_pinecone_batch(vectors)
        analyses = analyze_risk_batch(clauses, qresults)
    except Exception as e:
        print(f"❌ Pipeline error: {e}\n"); sys.exit(1)

    # ── results ───────────────────────────────────────────────────────────────
    W = 68   # line width

    print("=" * W)
    print(f"  CONTRACT RISK ANALYSIS — {len(analyses)} clauses")
    print("=" * W)

    for i, a in enumerate(analyses, 1):
        level   = a["risk_level"]
        icon    = RISK_ICON.get(level, "⚪")
        label   = RISK_LABEL.get(level, level)
        clause  = a["clause_text"]
        snippet = clause[:120].rstrip() + ("…" if len(clause) > 120 else "")
        expl    = a["explanation"]

        print()
        print(f"  {icon} {label}  |  Clause #{i}")
        print(f"  {'─' * (W - 4)}")
        # Clause text wrapped to W-4 chars
        for line in _wrap(snippet, W - 4):
            print(f"  {line}")
        print()
        # Explanation wrapped
        for line in _wrap(expl, W - 4):
            print(f"  {line}")

    # ── summary ───────────────────────────────────────────────────────────────
    s = get_risk_summary(analyses)
    print()
    print("=" * W)
    print(f"  SUMMARY")
    print(f"  🔴 High Risk    {s['high_risk_count']:>3}  ({s['high_risk_percentage']:4.1f}%)")
    print(f"  🟡 Medium Risk  {s['medium_risk_count']:>3}  ({s['medium_risk_percentage']:4.1f}%)")
    print(f"  🟢 Low Risk     {s['low_risk_count']:>3}  ({s['low_risk_percentage']:4.1f}%)")
    print("=" * W)
    print()


def _wrap(text: str, width: int):
    """Simple word-wrap helper."""
    words  = text.split()
    line   = ""
    lines  = []
    for w in words:
        if len(line) + len(w) + 1 <= width:
            line = (line + " " + w).lstrip() if line else w
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines or [""]


if __name__ == "__main__":
    main()
