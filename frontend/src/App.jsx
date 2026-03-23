import { useState } from 'react';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import LoadingIndicator from './components/LoadingIndicator';
import ResultsList from './components/ResultsList';
import './index.css';

function ErrorBanner({ message, onDismiss }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: 12,
      padding: '16px 18px',
      borderRadius: 10,
      background: 'rgba(239,68,68,0.1)',
      border: '1px solid rgba(239,68,68,0.3)',
      marginBottom: 20,
    }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 1 }}>
        <circle cx="12" cy="12" r="10" stroke="#ef4444" strokeWidth="2"/>
        <line x1="12" y1="8" x2="12" y2="12" stroke="#ef4444" strokeWidth="2" strokeLinecap="round"/>
        <line x1="12" y1="16" x2="12.01" y2="16" stroke="#ef4444" strokeWidth="2" strokeLinecap="round"/>
      </svg>
      <div style={{ flex: 1 }}>
        <p style={{ color: '#fca5a5', fontWeight: 600, fontSize: 13, marginBottom: 2 }}>
          Analysis Failed
        </p>
        <p style={{ color: '#f87171', fontSize: 12, lineHeight: 1.5 }}>{message}</p>
      </div>
      <button
        onClick={onDismiss}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: '#ef4444', padding: 2, flexShrink: 0,
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M18 6 6 18M6 6l12 12" stroke="#ef4444" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </button>
    </div>
  );
}

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading]           = useState(false);
  const [results, setResults]           = useState(null);
  const [error, setError]               = useState(null);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError(null);
    setResults(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Server error: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(
        err.message || 'Failed to analyze contract. Please check if the backend server is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResults(null);
    setError(null);
  };

  return (
    <div style={{ minHeight: '100vh', padding: '0 16px 48px' }}>
      <div style={{ maxWidth: 820, margin: '0 auto' }}>
        {/* Hero header */}
        <Header />

        {/* Main card */}
        <div style={{
          background: 'rgba(17,24,39,0.8)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: 18,
          padding: 'clamp(20px, 4vw, 36px)',
          boxShadow: '0 8px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(79,114,255,0.05)',
          backdropFilter: 'blur(12px)',
        }}>
          {/* Error */}
          {error && !loading && (
            <ErrorBanner message={error} onDismiss={() => setError(null)} />
          )}

          {/* Upload view */}
          {!loading && !results && (
            <FileUpload
              onFileSelect={handleFileSelect}
              selectedFile={selectedFile}
              onAnalyze={handleAnalyze}
              disabled={loading}
            />
          )}

          {/* Loading */}
          {loading && <LoadingIndicator />}

          {/* Results */}
          {results && !loading && (
            <>
              <ResultsList results={results} />

              {/* Reset button */}
              <div style={{ textAlign: 'center', marginTop: 28 }}>
                <button className="btn-ghost" onClick={handleReset}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"
                      stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M3 3v5h5" stroke="#94a3b8" strokeWidth="2"
                      strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  Analyze Another Contract
                </button>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <p style={{
          textAlign: 'center',
          color: '#334155',
          fontSize: 12,
          marginTop: 20,
          lineHeight: 1.6,
        }}>
          LexGuard · Powered by RoBERTa QA + Pinecone vector search · Runs locally
        </p>
      </div>
    </div>
  );
}

export default App;
