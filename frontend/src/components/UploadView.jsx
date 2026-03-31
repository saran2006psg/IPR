import React, { useCallback, useState, useEffect } from 'react';

export default function UploadView({ onFileSelect, selectedFile, onAnalyze, loading }) {
  const [dragging, setDragging] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.toLowerCase().endsWith('.pdf')) {
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileSelect(file);
  };

  useEffect(() => {
    let interval;
    if (loading) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 1500); // Progress through steps every 1.5 seconds purely for UX illusion
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const steps = [
    "Uploading document securely...",
    "Extracting text via OCR...",
    "Segmenting legal clauses...",
    "Querying vector database for precedents...",
    "Running structural risk analysis..."
  ];

  return (
    <div style={{ padding: '40px 48px', maxWidth: 800, margin: '0 auto', width: '100%' }}>
      <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-title)', marginBottom: 8 }}>Upload Contract</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 32 }}>Securely scan documents for liabilities, unbalanced terms, and compliance risks.</p>
      
      {!loading ? (
        <div className="card" style={{ padding: 40, textAlign: 'center' }}>
          <label
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border-strong)'}`,
              background: dragging ? '#f3f4f6' : 'var(--bg-main)',
              borderRadius: 8, padding: '60px 20px', cursor: 'pointer', transition: 'all 0.15s'
            }}
          >
            <input type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleInputChange} />
            <div style={{ width: 48, height: 48, background: '#e5e7eb', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            
            {!selectedFile ? (
              <>
                <p style={{ fontWeight: 600, color: 'var(--text-title)', fontSize: 16 }}>Click to upload or drag and drop</p>
                <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 4 }}>PDF, DOCX up to 10MB</p>
              </>
            ) : (
              <>
                <p style={{ fontWeight: 600, color: 'var(--text-title)', fontSize: 16 }}>{selectedFile.name}</p>
                <p style={{ color: 'var(--risk-low)', fontSize: 14, marginTop: 4, fontWeight: 500 }}>Ready for analysis</p>
              </>
            )}
          </label>

          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn-primary" disabled={!selectedFile} onClick={onAnalyze}>
              Scan Document
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: '40px', maxWidth: 480, margin: '0 auto' }}>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-title)', marginBottom: 24, textAlign: 'center' }}>Analyzing Document</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {steps.map((step, index) => {
              const status = index < loadingStep ? 'done' : index === loadingStep ? 'active' : 'pending';
              
              return (
                <div key={index} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ 
                    width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: status === 'done' ? 'var(--risk-low)' : status === 'active' ? '#eef2ff' : 'var(--bg-main)',
                    border: `1px solid ${status === 'done' ? 'var(--risk-low)' : status === 'active' ? 'var(--accent)' : 'var(--border)'}`
                  }}>
                    {status === 'done' && (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                    )}
                    {status === 'active' && (
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)', animation: 'pulse 1.5s infinite' }} />
                    )}
                  </div>
                  <span style={{ 
                    fontSize: 14, 
                    color: status === 'pending' ? 'var(--text-muted)' : 'var(--text-title)',
                    fontWeight: status === 'active' ? 500 : 400
                  }}>
                    {step}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
      `}</style>
    </div>
  );
}
