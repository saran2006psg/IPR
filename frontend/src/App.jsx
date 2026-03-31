import React, { useState } from 'react';
import UploadView from './components/UploadView';
import AnalysisView from './components/AnalysisView';

function TopNav({ currentView, setView, hasResults }) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      height: 64,
      background: '#ffffff',
      borderBottom: '1px solid var(--border)',
      flexShrink: 0
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 700, fontSize: 18, color: '#111827' }}>
          <div style={{ 
            width: 32, height: 32, borderRadius: 8, background: '#111827', 
            display: 'flex', alignItems: 'center', justifyContent: 'center' 
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L22 7L12 12L2 7L12 2Z" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          LexGuard
        </div>

        {/* Center Nav */}
        <nav style={{ display: 'flex', gap: 32, fontSize: 14, fontWeight: 500 }}>
          <button 
            onClick={() => setView('upload')}
            style={{ 
              background: 'none', border: 'none', cursor: 'pointer',
              color: currentView === 'upload' ? '#111827' : 'var(--text-muted)',
              borderBottom: currentView === 'upload' ? '2px solid #111827' : '2px solid transparent',
              padding: '21px 0 19px',
              transition: 'all 0.2s',
              outline: 'none'
            }}
          >
            Upload Contract
          </button>
          
          <button 
            onClick={() => setView('analysis')}
            disabled={!hasResults}
            style={{ 
              background: 'none', border: 'none', cursor: hasResults ? 'pointer' : 'not-allowed',
              color: currentView === 'analysis' ? '#111827' : 'var(--text-muted)',
              borderBottom: currentView === 'analysis' ? '2px solid #111827' : '2px solid transparent',
              padding: '21px 0 19px',
              transition: 'all 0.2s',
              opacity: hasResults ? 1 : 0.4,
              outline: 'none'
            }}
          >
            Risk Analysis
          </button>

          <button 
            onClick={() => setView('history')}
            style={{ 
              background: 'none', border: 'none', cursor: 'pointer',
              color: currentView === 'history' ? '#111827' : 'var(--text-muted)',
              borderBottom: currentView === 'history' ? '2px solid #111827' : '2px solid transparent',
              padding: '21px 0 19px',
              transition: 'all 0.2s',
              outline: 'none'
            }}
          >
            History
          </button>
        </nav>
      </div>

      {/* Right / User Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <button className="btn-ghost" style={{ padding: '6px 12px', fontSize: 13, borderRadius: 6 }}>
          Support
        </button>
        <div style={{ 
          width: 32, height: 32, borderRadius: '50%', 
          background: 'var(--border)', display: 'flex', alignItems: 'center', 
          justifyContent: 'center', fontSize: 13, fontWeight: 600, color: '#111827',
          cursor: 'pointer'
        }}>
          JD
        </div>
      </div>
    </header>
  );
}

export default function App() {
  const [currentView, setCurrentView] = useState('upload');
  
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  
  const [chatSessionId, setChatSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://localhost:8000/analyze', { method: 'POST', body: formData });
      if (!response.ok) throw new Error('Analysis failed');

      const data = await response.json();
      setResults(data.results);
      setChatSessionId(data.session_id || null);
      setChatMessages([]);
      setCurrentView('analysis');
    } catch (err) {
      console.error(err);
      alert('Analysis failed. Check console.');
    } finally {
      setLoading(false);
    }
  };

  const handleChatSend = async (question) => {
    if (!chatSessionId) return;
    
    const newMsg = { role: 'user', content: question };
    setChatMessages(p => [...p, newMsg]);
    setChatLoading(true);

    try {
      const resp = await fetch('http://localhost:8000/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: chatSessionId, question }),
      });
      const data = await resp.json();
      setChatMessages(data.history || []);
    } catch (err) {
      console.error(err);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden', background: 'var(--bg-base)' }}>
      <TopNav currentView={currentView} setView={setCurrentView} hasResults={!!results} />
      
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        {currentView === 'upload' && <UploadView 
          onFileSelect={setSelectedFile} 
          selectedFile={selectedFile} 
          onAnalyze={handleAnalyze} 
          loading={loading} 
        />}
        {currentView === 'analysis' && <AnalysisView 
          results={results} 
          chatSessionId={chatSessionId}
          chatMessages={chatMessages}
          onChatSend={handleChatSend}
          chatLoading={chatLoading}
        />}
        {currentView === 'history' && (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>History view coming soon.</div>
        )}
      </main>
    </div>
  );
}
