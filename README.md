# Legal Contract Risk Analyzer

<p align="center">
  <b>🏛️ AI-Powered Legal Contract Risk Analysis System</b>
</p>

<p align="center">
  Analyze legal contracts using semantic search and machine learning to identify high-risk clauses
</p>

---

## 📋 Overview

The Legal Contract Risk Analyzer is a complete end-to-end system for analyzing legal contracts using:

- **Vector Database**: Pinecone for semantic clause similarity search
- **Embeddings**: SentenceTransformers (all-mpnet-base-v2) for 768-dimensional embeddings
- **PDF Processing**: PyMuPDF for text extraction
- **Risk Analysis**: ML-based risk classification from a knowledge base of 9,447 legal clauses

---

## 🚀 Quick Start

### 1. Clone/Download the Project

```bash
cd d:\roberta-base
```

### 2. Run Setup Script

```bash
python scripts/setup.py
```

This will:

- ✅ Check Python version (3.8+ required)
- ✅ Create `.env` template if missing
- ✅ Install all dependencies from `requirements.txt`
- ✅ Verify installation
- ✅ Run system tests (if API key configured)

### 3. Configure Environment

Edit `.env` and add your Pinecone API key:

```
PINECONE_API_KEY=pcsk_xxxxxxxxxxxxxxxxxxxxx
```

### 4. Run Ingestion Pipeline (First Time Only)

```bash
python backend/scripts/ingest_pipeline.py
```

This loads 9,447 legal clauses into Pinecone (~5 minutes).

### 5. Test the System

```bash
# Create a sample contract
python backend/scripts/create_sample_contract.py

# Analyze the contract
python -m backend.retrieval_pipeline.main sample_employment_contract.pdf
```

### 6. Run the Backend API

```bash
python backend/api.py
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs

### 6.1 Run with Dedicated Model Server (Recommended)

For faster repeated analysis, run the QA model in a separate terminal so it stays loaded.

Terminal A (model service):

```bash
python backend/model_server.py
```

Terminal B (main API):

```bash
$env:MODEL_SERVER_ENABLED="true"
$env:MODEL_SERVER_URL="http://localhost:9000/qa"
$env:QA_BATCH_MODE_ENABLED="true"
$env:MODEL_SERVER_BATCH_SIZE="24"
python backend/api.py
```

In this mode, the main API calls the model service over HTTP and falls back to Pinecone-only similarity reasoning if the model service is temporarily unavailable.

Health endpoint now includes model-server status:

```json
{
  "status": "ok",
  "api": "ready",
  "model_server": "ready",
  "model_server_url": "http://localhost:9000/health",
  "timestamp": "2026-03-31T10:15:30.123456+00:00"
}
```

### 7. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173

---

## 📦 Installation (Manual)

If you prefer manual installation:

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from retrieval_pipeline import analyze_contract; print('✓ Success')"

# Run tests
python test_system.py
```

---

## 🏗️ Project Structure

```
roberta-base/
├── requirements.txt                 # All dependencies (consolidated)
├── setup.py                         # Automated setup script
├── .env                             # Environment variables (API keys)
│
├── ingest_pipeline.py              # Stage 1: Load clauses into Pinecone
├── legal_contract_clauses.csv      # 9,447 legal clauses dataset
│
├── retrieval_pipeline/             # Stage 2: Analyze contracts
│   ├── __init__.py                 # Package exports
│   ├── config.py                   # Configuration constants
│   ├── pdf_extractor.py            # PDF text extraction
│   ├── clause_segmenter.py         # Clause segmentation
│   ├── embedder.py                 # Embedding generation
│   ├── retriever.py                # Pinecone queries
│   ├── risk_analyzer.py            # Risk classification
│   └── main.py                     # CLI orchestrator
│
├── test_system.py                  # Comprehensive system tests
├── create_sample_contract.py       # Generate test PDFs
│
├── README.md                        # This file
├── README_RETRIEVAL.md             # Retrieval pipeline docs
└── TESTING_GUIDE.md                # Testing instructions
```

---

## 💻 Usage

### Command-Line Interface

```bash
# Basic analysis
python -m retrieval_pipeline.main contract.pdf

# Verbose mode (shows progress)
python -m retrieval_pipeline.main --verbose contract.pdf

# Summary only
python -m retrieval_pipeline.main --quiet contract.pdf
```

### Python API

```python
from retrieval_pipeline import analyze_contract

# Analyze a contract
analyses = analyze_contract("contract.pdf", verbose=True)

# Print results
for analysis in analyses:
    print(f"Risk: {analysis['risk_level']}")
    print(f"Clause: {analysis['contract_clause'][:100]}...")
    print(f"Explanation: {analysis['explanation']}\n")
```

### Step-by-Step Processing

```python
from retrieval_pipeline import (
    extract_pdf_text,
    segment_clauses,
    embed_clauses,
    query_pinecone_batch,
    analyze_risk_batch,
    get_risk_summary
)

# Extract and segment
text = extract_pdf_text("contract.pdf")
clauses = segment_clauses(text)

# Generate embeddings
vectors = embed_clauses(clauses)

# Query Pinecone
results = query_pinecone_batch(vectors)

# Analyze risk
analyses = analyze_risk_batch(clauses, results)
summary = get_risk_summary(analyses)

print(f"High risk clauses: {summary['high_risk_count']}")
```

---

## 🧪 Testing

### Full System Test

```bash
python test_system.py
```

Tests:

1. ✅ Environment configuration
2. ✅ Package imports
3. ✅ Pinecone connection
4. ✅ Embedding generation
5. ✅ Vector queries
6. ✅ Clause segmentation
7. ✅ Risk analysis

### Create Sample Contract

```bash
# Generate PDF
python create_sample_contract.py

# Analyze it
python -m retrieval_pipeline.main sample_employment_contract.pdf
```

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed testing instructions.

---

## 📊 System Components

### Stage 1: Ingestion Pipeline

- **Input**: CSV file with 9,447 legal clauses
- **Process**: Generate embeddings → Upload to Pinecone
- **Output**: Populated vector database
- **Runtime**: ~5 minutes

### Stage 2: Retrieval Pipeline

- **Input**: Contract PDF
- **Process**: Extract text → Segment → Embed → Query → Analyze
- **Output**: Risk analysis report
- **Runtime**: ~10-30 seconds per contract

---

## ⚙️ Configuration

Edit `retrieval_pipeline/config.py` to customize:

```python
# Pinecone settings
INDEX_NAME = "contract-risk-db"
TOP_K = 5  # Similar clauses to retrieve

# Risk analysis
SIMILARITY_THRESHOLD = 0.7  # Minimum relevance score

# Clause segmentation
MIN_CLAUSE_LENGTH = 20  # Minimum characters
```

---

## 📈 Output Format

### Risk Levels

- 🔴 **HIGH**: Similar to known high-risk clauses
- 🟡 **MEDIUM**: Moderate risk factors
- 🟢 **LOW**: Standard/low-risk clauses

### Example Output

```
================================================================================
📊 RISK ANALYSIS SUMMARY
================================================================================

Total Clauses Analyzed: 10

  🔴 HIGH RISK:     3 ( 30.0%)
  🟡 MEDIUM RISK:   4 ( 40.0%)
  🟢 LOW RISK:      3 ( 30.0%)
================================================================================
```

---

## 🔧 Troubleshooting

### Common Issues

**1. "PINECONE_API_KEY not found"**

- Solution: Edit `.env` file and add your API key

**2. "Index not found"**

- Solution: Run `python ingest_pipeline.py`

**3. "No clauses extracted"**

- PDF may be scanned (no text layer)
- Use OCR or try a different PDF

**4. Import errors**

- Solution: `pip install -r requirements.txt`

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for more troubleshooting.

---

## 📚 Documentation

- [README_RETRIEVAL.md](README_RETRIEVAL.md) - Detailed retrieval pipeline documentation
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Step-by-step testing guide

---

## 🛠️ Requirements

- Python 3.8+
- Pinecone API key (free tier available)
- ~2GB disk space (for model downloads)
- ~4GB RAM (8GB recommended)

---

## 📝 Dependencies

See [requirements.txt](requirements.txt) for complete list.

Core dependencies:

- `sentence-transformers>=2.2.0`
- `pinecone>=5.0.0`
- `PyMuPDF>=1.23.0`
- `pandas>=2.0.0`
- `torch>=2.0.0`

---

## 🎯 Use Cases

- **Legal Review**: Automate contract risk screening
- **Compliance**: Identify non-standard clauses
- **Due Diligence**: Batch analyze contracts
- **Contract Negotiation**: Flag high-risk terms
- **Learning**: Study legal clause patterns

---

## 📄 License

This project is provided as-is for educational and research purposes.

---

## 🙏 Acknowledgments

- Dataset: 9,447 legal contract clauses
- Embeddings: sentence-transformers/all-mpnet-base-v2
- Vector DB: Pinecone
- PDF Processing: PyMuPDF

---

**Version**: 1.0.0  
**Last Updated**: March 11, 2026  
**Status**: ✅ Production Ready
