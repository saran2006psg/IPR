"""
Test script for Legal Contract Risk Analyzer - Retrieval Pipeline

This script tests each component of the system step-by-step to verify
everything is working correctly.
"""

import os
import sys

print("=" * 80)
print("🧪 LEGAL CONTRACT RISK ANALYZER - SYSTEM TEST")
print("=" * 80)

# Test 1: Check environment variables
print("\n[TEST 1] Checking environment configuration...")
print("-" * 80)

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("PINECONE_API_KEY")
    if api_key:
        print(f"✓ PINECONE_API_KEY found: {api_key[:20]}...")
    else:
        print("❌ PINECONE_API_KEY not found in .env file!")
        print("   Please add: PINECONE_API_KEY=your-key-here")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error loading .env: {e}")
    sys.exit(1)

# Test 2: Check imports
print("\n[TEST 2] Testing package imports...")
print("-" * 80)

try:
    from retrieval_pipeline import (
        extract_pdf_text,
        segment_clauses,
        embed_clause,
        query_pinecone,
        analyze_risk,
        analyze_contract
    )
    print("✓ All retrieval_pipeline imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Check Pinecone connection
print("\n[TEST 3] Testing Pinecone connection...")
print("-" * 80)

try:
    from retrieval_pipeline import get_index_stats
    stats = get_index_stats()
    
    total_vectors = stats.get('total_vector_count', 0)
    print(f"✓ Connected to Pinecone successfully")
    print(f"  Index: contract-risk-db")
    print(f"  Total vectors: {total_vectors:,}")
    
    if total_vectors == 0:
        print("\n⚠️  WARNING: Index has 0 vectors!")
        print("   You need to run the ingestion pipeline first:")
        print("   python ingest_pipeline.py")
    elif total_vectors != 9447:
        print(f"\n⚠️  WARNING: Expected 9,447 vectors but found {total_vectors}")
    else:
        print("✓ Index has expected number of vectors (9,447)")
        
except Exception as e:
    print(f"❌ Pinecone connection failed: {e}")
    print("\n   Possible issues:")
    print("   1. Wrong API key in .env file")
    print("   2. Index 'contract-risk-db' doesn't exist")
    print("   3. Need to run: python ingest_pipeline.py")
    sys.exit(1)

# Test 4: Test embedding generation
print("\n[TEST 4] Testing embedding generation...")
print("-" * 80)

try:
    from retrieval_pipeline import embed_clause, get_embedding_dimension
    
    test_clause = "This agreement shall be governed by the laws of New York."
    print(f"  Test clause: '{test_clause}'")
    
    vector = embed_clause(test_clause)
    
    print(f"✓ Embedding generated successfully")
    print(f"  Dimension: {len(vector)} (expected: {get_embedding_dimension()})")
    print(f"  Sample values: [{vector[0]:.4f}, {vector[1]:.4f}, {vector[2]:.4f}, ...]")
    
    if len(vector) != 768:
        print(f"❌ Wrong dimension! Expected 768, got {len(vector)}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Embedding generation failed: {e}")
    sys.exit(1)

# Test 5: Test Pinecone query
print("\n[TEST 5] Testing Pinecone query...")
print("-" * 80)

try:
    from retrieval_pipeline import query_pinecone
    
    # Use the embedding from Test 4
    results = query_pinecone(vector, top_k=3)
    
    if hasattr(results, 'matches'):
        matches = results.matches
        print(f"✓ Query successful - found {len(matches)} matches")
        
        if len(matches) > 0:
            print("\n  Top match:")
            match = matches[0]
            print(f"    Score: {match.score:.4f}")
            
            if hasattr(match, 'metadata'):
                metadata = match.metadata
                print(f"    Severity: {metadata.get('severity', 'N/A')}")
                print(f"    Type: {metadata.get('clause_type', 'N/A')}")
                clause_text = metadata.get('clause_text', '')
                if clause_text:
                    print(f"    Text: {clause_text[:100]}...")
            else:
                print("⚠️  No metadata found")
    else:
        print("❌ Query returned unexpected format")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Pinecone query failed: {e}")
    sys.exit(1)

# Test 6: Test clause segmentation
print("\n[TEST 6] Testing clause segmentation...")
print("-" * 80)

try:
    from retrieval_pipeline import segment_clauses
    
    sample_contract = """
    1. PARTIES
    This Agreement is entered into between Company A and Company B.
    
    2. TERM
    The term of this Agreement shall be twelve (12) months from the Effective Date.
    
    3. TERMINATION
    Either party may terminate this Agreement with thirty (30) days written notice.
    
    4. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of New York.
    """
    
    clauses = segment_clauses(sample_contract)
    print(f"✓ Segmentation successful")
    print(f"  Input text: {len(sample_contract)} characters")
    print(f"  Clauses found: {len(clauses)}")
    
    for i, clause in enumerate(clauses, 1):
        print(f"    {i}. {clause[:60]}...")
        
except Exception as e:
    print(f"❌ Clause segmentation failed: {e}")
    sys.exit(1)

# Test 7: Test risk analysis
print("\n[TEST 7] Testing risk analysis...")
print("-" * 80)

try:
    from retrieval_pipeline import analyze_risk
    
    # Use the query results from Test 5
    analysis = analyze_risk(test_clause, results)
    
    print(f"✓ Risk analysis successful")
    print(f"  Clause key present: {'clause_text' in analysis}")
    print(f"  Risk Level: {analysis['risk_level']}")
    print(f"  Explanation: {analysis['explanation']}")
    print(f"  Similar clauses found: {len(analysis['similar_clauses'])}")
    
except Exception as e:
    print(f"❌ Risk analysis failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
print("\nYour system is ready to analyze contracts!")
print("\nNext steps:")
print("  1. Get a contract PDF file")
print("  2. Run: python -m retrieval_pipeline.main contract.pdf")
print("\nOr use the sample text generator:")
print("  python create_sample_contract.py")
print("\n" + "=" * 80)
