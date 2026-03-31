#!/usr/bin/env python
"""
PHASE 1 Implementation Quick Test Script
Tests quality scoring, answer validation, and configuration
Run this before starting the servers to verify Phase 1 is working correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from retrieval_pipeline.config import (
    CHAT_MIN_CONFIDENCE, 
    SUMMARY_MIN_CONFIDENCE,
    MIN_ANSWER_LENGTH,
    MIN_ANSWER_FOR_FALLBACK
)
from retrieval_pipeline.llm_reasoner import (
    _score_answer_quality,
    _is_incomplete_answer,
    _normalize_answer
)

def test_config():
    """Verify Phase 1 configuration changes"""
    print("\n" + "="*60)
    print("TEST 1: Configuration Verification")
    print("="*60)
    
    checks = [
        ("CHAT_MIN_CONFIDENCE", CHAT_MIN_CONFIDENCE, -0.5, "Should be -0.5 (was -2.5)"),
        ("SUMMARY_MIN_CONFIDENCE", SUMMARY_MIN_CONFIDENCE, 0.5, "Should be 0.5"),
        ("MIN_ANSWER_LENGTH", MIN_ANSWER_LENGTH, 8, "Should be 8 (was 2)"),
        ("MIN_ANSWER_FOR_FALLBACK", MIN_ANSWER_FOR_FALLBACK, 10, "Should be 10"),
    ]
    
    all_passed = True
    for name, actual, expected, desc in checks:
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        print(f"{status} | {name}: {actual} ({desc})")
        if actual != expected:
            all_passed = False
    
    return all_passed


def test_quality_scoring():
    """Test answer quality scoring function"""
    print("\n" + "="*60)
    print("TEST 2: Answer Quality Scoring")
    print("="*60)
    
    test_cases = [
        # (answer, confidence, expected_range, description)
        ("The governing law is New York.", 1.5, (0.8, 1.0), "✅ Excellent answer"),
        ("30 days", 0.8, (0.5, 0.8), "✅ Good short answer"),
        ("No", -1.0, (0.0, 0.3), "❌ Too short (should be rejected)"),
        ("and the contract", -0.5, (0.0, 0.3), "❌ Starts with conjunction (truncated)"),
        ("termination clause (", 0.5, (0.0, 0.3), "❌ Unclosed paren (incomplete)"),
        ("If the party wishes to terminate,", 0.2, (0.0, 0.4), "❌ Ends with comma (incomplete)"),
    ]
    
    all_passed = True
    for answer, conf, (low, high), desc in test_cases:
        score = _score_answer_quality(answer, conf)
        in_range = low <= score <= high
        status = "✅ PASS" if in_range else "❌ FAIL"
        print(f"{status} | {desc}")
        print(f"      Answer: '{answer[:40]}...' | Conf: {conf:.1f} → Quality: {score:.2f} (expected {low:.1f}-{high:.1f})")
        if not in_range:
            all_passed = False
    
    return all_passed


def test_incomplete_detection():
    """Test incomplete answer detection"""
    print("\n" + "="*60)
    print("TEST 3: Incomplete Answer Detection")
    print("="*60)
    
    test_cases = [
        ("and the termination", True, "Starts with conjunction"),
        ("or requires notice", True, "Starts with conjunction"),
        ("The notice must be in writing(", True, "Unclosed parenthesis"),
        ("30 days,", True, "Ends with comma"),
        ("Governed by New York law", False, "Complete, valid answer"),
        ("The party can terminate", False, "Complete answer"),
    ]
    
    all_passed = True
    for answer, should_be_incomplete, desc in test_cases:
        is_incomplete = _is_incomplete_answer(answer)
        status = "✅ PASS" if is_incomplete == should_be_incomplete else "❌ FAIL"
        result = "DETECTED as incomplete" if is_incomplete else "NOT detected as incomplete"
        print(f"{status} | {desc}")
        print(f"      '{answer}' → {result}")
        if is_incomplete != should_be_incomplete:
            all_passed = False
    
    return all_passed


def test_answer_normalization():
    """Test answer normalization/cleanup"""
    print("\n" + "="*60)
    print("TEST 4: Answer Normalization")
    print("="*60)
    
    test_cases = [
        ("and  the   contract   is", "the contract is", "Removes leading conjunction + collapses spaces"),
        ("or regarding payment", "regarding payment", "Removes 'or'"),
        ("  spaces  everywhere  ", "spaces everywhere", "Strips and collapses whitespace"),
        ("Normal answer", "Normal answer", "Leave valid answers unchanged"),
    ]
    
    all_passed = True
    for dirty, expected, desc in test_cases:
        cleaned = _normalize_answer(dirty)
        status = "✅ PASS" if cleaned == expected else "❌ FAIL"
        print(f"{status} | {desc}")
        print(f"      Before: '{dirty}'")
        print(f"      After:  '{cleaned}'")
        print(f"      Expect: '{expected}'")
        if cleaned != expected:
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("PHASE 1 IMPLEMENTATION TEST SUITE")
    print("="*60)
    
    results = []
    
    results.append(("Configuration", test_config()))
    results.append(("Quality Scoring", test_quality_scoring()))
    results.append(("Incomplete Detection", test_incomplete_detection()))
    results.append(("Answer Normalization", test_answer_normalization()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ ALL PASSED" if passed else "❌ SOME FAILED"
        print(f"{status} | {test_name}")
    
    all_passed = all(p for _, p in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Phase 1 implementation is correct!")
        print("="*60)
        print("\nYou can now start the servers and test with real contract documents.")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Fix issues before starting servers")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
