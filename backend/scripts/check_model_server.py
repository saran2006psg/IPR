#!/usr/bin/env python3
"""Simple smoke-test script for the QA model server.

Usage:
    python backend/scripts/check_model_server.py
    python backend/scripts/check_model_server.py --qa-url http://localhost:9000/qa
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional


def _load_runtime_config() -> tuple[str, float]:
    """Load model-server URL and timeout from project config when available."""
    backend_dir = Path(__file__).resolve().parent.parent
    repo_root = backend_dir.parent

    # Keep imports local so script still runs even when optional deps are missing.
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(repo_root / ".env")
    except Exception:
        pass

    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        from retrieval_pipeline.config import MODEL_SERVER_TIMEOUT_SEC, MODEL_SERVER_URL
        return str(MODEL_SERVER_URL), float(MODEL_SERVER_TIMEOUT_SEC)
    except Exception:
        return "http://localhost:9000/qa", 8.0


def _json_request(url: str, payload: Optional[Dict[str, Any]], timeout_sec: float) -> Dict[str, Any]:
    """Issue GET/POST JSON request and parse JSON response."""
    data = None
    method = "GET"
    if payload is not None:
        method = "POST"
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=timeout_sec) as response:
        return json.loads(response.read().decode("utf-8"))


def _to_base_url(qa_url: str) -> str:
    qa_url = qa_url.rstrip("/")
    if qa_url.endswith("/qa"):
        return qa_url[:-3]
    return qa_url


def main() -> int:
    default_qa_url, default_timeout = _load_runtime_config()

    parser = argparse.ArgumentParser(description="Smoke-test the dedicated QA model server.")
    parser.add_argument("--qa-url", default=default_qa_url, help="QA endpoint URL (default: config MODEL_SERVER_URL)")
    parser.add_argument("--timeout", type=float, default=default_timeout, help="HTTP timeout in seconds")
    parser.add_argument("--wait-seconds", type=int, default=30, help="Max seconds to wait for health status=ok")
    args = parser.parse_args()

    qa_url = args.qa_url.rstrip("/")
    base_url = _to_base_url(qa_url)
    health_url = f"{base_url}/health"
    batch_url = f"{base_url}/qa_batch"

    print("=" * 72)
    print("MODEL SERVER SMOKE TEST")
    print("=" * 72)
    print(f"QA URL      : {qa_url}")
    print(f"Health URL  : {health_url}")
    print(f"Batch URL   : {batch_url}")
    print(f"Timeout(sec): {args.timeout}")

    # Step 1: wait for health ready
    print("\n[1/3] Checking health endpoint...")
    health_payload: Optional[Dict[str, Any]] = None
    last_error = ""
    deadline = time.time() + max(1, args.wait_seconds)

    while time.time() < deadline:
        try:
            health_payload = _json_request(health_url, payload=None, timeout_sec=args.timeout)
            status = str(health_payload.get("status", "unknown"))
            if status == "ok":
                print(f"PASS: Health status is ok -> {health_payload}")
                break
            print(f"INFO: Health status is '{status}', waiting...")
        except Exception as exc:  # pragma: no cover - diagnostic path
            last_error = str(exc)
            print(f"INFO: health check not ready yet ({last_error})")

        time.sleep(1)

    if not health_payload or str(health_payload.get("status", "unknown")) != "ok":
        print("FAIL: Model server health did not reach status=ok within wait window.")
        if last_error:
            print(f"Last error: {last_error}")
        return 2

    # Step 2: single QA request
    print("\n[2/3] Running /qa inference check...")
    single_payload = {
        "question": "What is the governing law?",
        "context": "This Agreement shall be governed by the laws of New York.",
    }

    try:
        qa_response = _json_request(qa_url, payload=single_payload, timeout_sec=args.timeout)
        answer = str(qa_response.get("answer", "")).strip()
        confidence = qa_response.get("confidence")

        if not isinstance(confidence, (int, float)):
            print(f"FAIL: /qa returned invalid confidence field: {qa_response}")
            return 3

        print(f"PASS: /qa returned answer='{answer}' confidence={float(confidence):.2f}")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
        print(f"FAIL: /qa request failed: {exc}")
        return 3

    # Step 3: batch QA request
    print("\n[3/3] Running /qa_batch inference check...")
    batch_payload = {
        "requests": [
            {
                "question": "What is the governing law?",
                "context": "This Agreement shall be governed by the laws of New York.",
            },
            {
                "question": "What is the notice period?",
                "context": "Either party may terminate this Agreement with 30 days written notice.",
            },
        ]
    }

    try:
        batch_response = _json_request(batch_url, payload=batch_payload, timeout_sec=args.timeout)
        responses = batch_response.get("responses", [])

        if not isinstance(responses, list) or len(responses) != 2:
            print(f"FAIL: /qa_batch returned unexpected payload: {batch_response}")
            return 4

        print("PASS: /qa_batch returned 2 responses")
        for idx, item in enumerate(responses, start=1):
            answer = str(item.get("answer", "")).strip()
            confidence = float(item.get("confidence", -999.0))
            print(f"  [{idx}] answer='{answer}' confidence={confidence:.2f}")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
        print(f"FAIL: /qa_batch request failed: {exc}")
        return 4

    print("\nSUCCESS: Model server is running and accepting both single + batch requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
