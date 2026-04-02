# System Overview

## Purpose

The IPR system is an AI-assisted Contract Risk Analyzer that helps users review legal contracts by:

- Extracting text from uploaded PDF contracts
- Segmenting content into clauses
- Retrieving semantically similar reference clauses from a legal knowledge base
- Assigning clause-level risk labels with explanation
- Supporting clause-aware follow-up Q&A through a chat assistant

The platform is designed to provide practical legal review support with traceable, clause-level evidence.

## Core Capabilities

1. Contract ingestion from PDF files
2. OCR fallback for scanned pages
3. Clause segmentation and normalization
4. Embedding-based retrieval against indexed legal clauses
5. Risk analysis using a fine-tuned RoBERTa reasoning stack
6. Agreement-type and user-role contextualization
7. Chat-based interaction grounded in analyzed contract clauses
8. Session persistence for conversational continuity

## Users and Modes

The system currently supports role-aware analysis modes such as:

- Buyer / Seller perspectives for sales agreements
- Acquirer / Target / Shareholder perspectives for merger workflows
- Landlord / Tenant perspectives for rental workflows

Role context influences how risk explanations are generated and prioritized.

## High-Level Processing Stages

1. Upload and validation
2. Text extraction from PDF
3. Clause segmentation
4. Clause embedding
5. Similarity retrieval from vector index
6. Clause risk reasoning
7. Result packaging for UI and chat session creation

## Main Deliverables per Analysis

For each clause, the system returns:

- Original clause text
- Risk level (`HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`)
- Explanation text
- Top similar reference clauses with metadata and similarity score

For each analyzed contract, the system can also provide:

- Aggregate risk summary
- Persistent chat session ID
- Clause citations used in chat answers

## Technology Summary

- Backend API: FastAPI
- Retrieval pipeline: Python modules in `backend/retrieval_pipeline`
- Vector retrieval: Pinecone index
- Embeddings: sentence-transformers `all-mpnet-base-v2`
- QA and reasoning model: fine-tuned local RoBERTa model assets in `models/roberta-base`
- Frontend: React + Vite
- Session persistence: SQLite database
