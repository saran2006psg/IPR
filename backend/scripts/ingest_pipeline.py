#!/usr/bin/env python3
"""
Contract Risk Analysis - Data Ingestion Pipeline for RAG System

This script ingests legal contract clauses from a CSV file, generates embeddings using 
SentenceTransformer, and uploads vectors to Pinecone for semantic search.

Dataset: 9,447 legal contract clauses with risk levels
Embedding Model: sentence-transformers/all-mpnet-base-v2 (768 dimensions)
Vector Database: Pinecone

Installation:
    pip install -r requirements.txt

Usage:
    # Option 1: Create a .env file in the same directory
    echo "PINECONE_API_KEY=your-api-key-here" > .env
    
    # Option 2: Set environment variable
    export PINECONE_API_KEY="your-api-key-here"  # Linux/Mac
    set PINECONE_API_KEY=your-api-key-here       # Windows CMD
    $env:PINECONE_API_KEY="your-api-key-here"    # Windows PowerShell
    
    python ingest_pipeline.py
"""

import os
import re
import sys
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

# Load environment variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use environment variables directly
    pass


# Configuration
CSV_FILEPATH = "../data/legal_contract_clauses.csv"
INDEX_NAME = "contract-risk-db"
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIMENSION = 768
BATCH_SIZE = 100
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load the legal contract clauses dataset from CSV file.
    
    Args:
        filepath: Path to the CSV file containing contract clauses
        
    Returns:
        DataFrame with columns: clause_text, clause_type, risk_level
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        pd.errors.EmptyDataError: If CSV file is empty
    """
    print(f"\n[1/5] Loading dataset from '{filepath}'...")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Validate required columns
    required_columns = ['clause_text', 'clause_type', 'risk_level']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    print(f"✓ Loaded {len(df):,} contract clauses")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    
    # Display risk level distribution
    risk_dist = df['risk_level'].value_counts().sort_index()
    print(f"  Risk distribution: {dict(risk_dist)}")
    
    return df


def preprocess_text(text: Any) -> str:
    """
    Clean and preprocess clause text for embedding generation.
    
    The CSV contains clauses extracted from PDFs with excessive whitespace,
    multiple newlines, and inconsistent formatting.
    
    Args:
        text: Raw clause text (can be str, float/NaN, or None)
        
    Returns:
        Cleaned text string with normalized whitespace
    """
    # Handle NaN, None, or non-string values
    if pd.isna(text) or text is None:
        return ""
    
    text = str(text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple whitespace characters (spaces, tabs, newlines) with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove any remaining control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text


def generate_embeddings(texts: List[str], model_name: str = EMBEDDING_MODEL) -> np.ndarray:
    """
    Generate embeddings for a list of text strings using SentenceTransformer.
    
    Args:
        texts: List of preprocessed clause texts
        model_name: Name/path of the SentenceTransformer model
        
    Returns:
        NumPy array of shape (num_texts, embedding_dimension)
    """
    print(f"\n[3/5] Generating embeddings using '{model_name}'...")
    print(f"  Loading model...")
    
    # Load the embedding model
    model = SentenceTransformer(model_name)
    
    print(f"  Encoding {len(texts):,} clauses (this may take a few minutes)...")
    
    # Generate embeddings with progress bar
    # normalize_embeddings=True ensures unit vectors (better for cosine similarity)
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,  # Internal batch size for encoding
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    
    print(f"✓ Generated embeddings with shape: {embeddings.shape}")
    
    return embeddings


def init_pinecone() -> Any:
    """
    Initialize Pinecone client and create/connect to the index.
    
    Reads PINECONE_API_KEY from environment variable.
    Creates the index if it doesn't exist.
    
    Returns:
        Pinecone Index object ready for upsert operations
        
    Raises:
        ValueError: If PINECONE_API_KEY environment variable is not set
    """
    print(f"\n[4/5] Initializing Pinecone connection...")
    
    # Get API key from environment
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError(
            "PINECONE_API_KEY environment variable not set.\n"
            "Set it using one of these methods:\n\n"
            "Option 1 - .env file (recommended):\n"
            "  Create a .env file with: PINECONE_API_KEY=your-key\n\n"
            "Option 2 - Environment variable:\n"
            "  export PINECONE_API_KEY='your-key'  (Linux/Mac)\n"
            "  set PINECONE_API_KEY=your-key       (Windows CMD)\n"
            "  $env:PINECONE_API_KEY='your-key'    (Windows PowerShell)"
        )
    
    # Initialize Pinecone client (v3+ API)
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists
    existing_indexes = pc.list_indexes().names()
    
    if INDEX_NAME not in existing_indexes:
        print(f"  Index '{INDEX_NAME}' does not exist. Creating...")
        
        # Create serverless index
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=PINECONE_CLOUD,
                region=PINECONE_REGION
            )
        )
        print(f"✓ Created index '{INDEX_NAME}'")
    else:
        print(f"✓ Connected to existing index '{INDEX_NAME}'")
    
    # Connect to the index
    index = pc.Index(INDEX_NAME)
    
    # Display index stats
    stats = index.describe_index_stats()
    print(f"  Current vector count: {stats.get('total_vector_count', 0):,}")
    
    return index


def store_vectors(
    index: Any,
    ids: List[str],
    embeddings: np.ndarray,
    metadatas: List[Dict[str, Any]],
    batch_size: int = BATCH_SIZE
) -> None:
    """
    Upload vectors to Pinecone index in batches with progress logging.
    
    Args:
        index: Pinecone Index object
        ids: List of unique IDs for each vector
        embeddings: NumPy array of embedding vectors
        metadatas: List of metadata dictionaries
        batch_size: Number of vectors to upload per batch
    """
    print(f"\n[5/5] Uploading {len(ids):,} vectors to Pinecone...")
    print(f"  Batch size: {batch_size}")
    
    total_records = len(ids)
    num_batches = (total_records + batch_size - 1) // batch_size
    
    # Process in batches
    for i in range(0, total_records, batch_size):
        batch_end = min(i + batch_size, total_records)
        batch_num = (i // batch_size) + 1
        
        # Prepare batch data
        batch_ids = ids[i:batch_end]
        batch_embeddings = embeddings[i:batch_end].tolist()
        batch_metadatas = metadatas[i:batch_end]
        
        # Create vectors in the format Pinecone expects
        vectors = [
            {
                "id": str(vec_id),
                "values": vec_values,
                "metadata": vec_metadata
            }
            for vec_id, vec_values, vec_metadata in zip(
                batch_ids, batch_embeddings, batch_metadatas
            )
        ]
        
        # Upsert to Pinecone
        try:
            index.upsert(vectors=vectors)
            print(f"  ✓ Uploaded batch {batch_num}/{num_batches} (records {i+1:,}-{batch_end:,})")
        except Exception as e:
            print(f"  ✗ Error uploading batch {batch_num}: {e}")
            raise
    
    print(f"✓ Successfully uploaded all {total_records:,} vectors")


def main():
    """
    Main pipeline orchestration function.
    
    Executes the complete data ingestion pipeline:
    1. Load dataset from CSV
    2. Preprocess text
    3. Generate embeddings
    4. Initialize Pinecone
    5. Upload vectors to Pinecone
    """
    print("=" * 70)
    print("Contract Risk Analysis - Data Ingestion Pipeline")
    print("=" * 70)
    
    try:
        # Step 1: Load dataset
        df = load_dataset(CSV_FILEPATH)
        
        # Step 2: Preprocess text
        print(f"\n[2/5] Preprocessing clause text...")
        df['clause_text_cleaned'] = df['clause_text'].apply(preprocess_text)
        
        # Filter out empty clauses
        original_count = len(df)
        df = df[df['clause_text_cleaned'].str.len() > 0].reset_index(drop=True)
        filtered_count = original_count - len(df)
        
        if filtered_count > 0:
            print(f"  Filtered out {filtered_count} empty clauses")
        print(f"✓ Preprocessed {len(df):,} clauses")
        
        # Generate IDs (use row index as string)
        ids = [str(i) for i in range(len(df))]
        
        # Prepare metadata (map risk_level → severity)
        print(f"  Building metadata records...")
        metadatas = [
            {
                "clause_text": row['clause_text_cleaned'],
                "severity": row['risk_level'],  # Map risk_level to severity
                "clause_type": row['clause_type']
            }
            for _, row in df.iterrows()
        ]
        print(f"✓ Created {len(metadatas):,} metadata records")
        
        # Step 3: Generate embeddings
        texts = df['clause_text_cleaned'].tolist()
        embeddings = generate_embeddings(texts)
        
        # Step 4: Initialize Pinecone
        index = init_pinecone()
        
        # Step 5: Upload vectors
        store_vectors(index, ids, embeddings, metadatas)
        
        # Final summary
        print("\n" + "=" * 70)
        print("✓ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
        # Display final index stats
        stats = index.describe_index_stats()
        print(f"\nPinecone Index Stats:")
        print(f"  Index name: {INDEX_NAME}")
        print(f"  Total vectors: {stats.get('total_vector_count', 0):,}")
        print(f"  Dimension: {EMBEDDING_DIMENSION}")
        
        print(f"\nExample vector record format:")
        print(f"  ID: '{ids[0]}'")
        print(f"  Values: [{embeddings[0][:3].tolist()}, ...] (768-dim)")
        print(f"  Metadata: {metadatas[0]}")
        
        print(f"\n✓ All {len(ids):,} contract clauses successfully indexed!")
        
    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
