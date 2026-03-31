import { useEffect, useState } from 'react';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import LoadingIndicator from './components/LoadingIndicator';
import ResultsList from './components/ResultsList';
import ChatPanel from './components/ChatPanel';
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

function SummaryDisplay({ summary }) {
  const lines = summary.split('\n');
  const sections = [];
  let currentSection = null;

  lines.forEach((line, index) => {
    if (line.startsWith('## ')) {
      // Main title
      sections.push({
        type: 'title',
        content: line.replace('## ', ''),
        key: `title-${index}`
      });
    } else if (line.startsWith('**') && line.endsWith(':**')) {
      // Section header
      currentSection = line.replace(/\*\*/g, '').replace(':', '');
      sections.push({
        type: 'section',
        content: currentSection,
        key: `section-${index}`
      });
    } else if (line.startsWith('- ')) {
      // List item
      const content = line.substring(2);
      if (content.includes(':')) {
        // Risk distribution item
        const [label, value] = content.split(': ');
        sections.push({
          type: 'risk-item',
          label,
          value,
          key: `risk-${index}`
        });
      } else if (content.startsWith('**')) {
        // Bold list item
        sections.push({
          type: 'bold-item',
          content: content.replace(/\*\*/g, ''),
          key: `bold-${index}`
        });
      } else {
        // Regular list item
        sections.push({
          type: 'list-item',
          content,
          key: `list-${index}`
        });
      }
    } else if (line.startsWith('  ')) {
      // Indented content (like numbered lists)
      const content = line.trim();
      if (/^\d+\./.test(content)) {
        // Numbered item
        sections.push({
          type: 'numbered-item',
          content: content.replace(/^\d+\.\s*/, ''),
          key: `numbered-${index}`
        });
      } else {
        // Regular indented text
        sections.push({
          type: 'indented',
          content,
          key: `indented-${index}`
        });
      }
    } else if (line.trim() && !line.startsWith('**')) {
      // Regular paragraph text
      sections.push({
        type: 'paragraph',
        content: line.trim(),
        key: `para-${index}`
      });
    }
  });

  return (
    <div>
      {sections.map(section => {
        switch (section.type) {
          case 'title':
            return (
              <h3 key={section.key} style={{
                fontSize: 18,
                fontWeight: 700,
                color: '#4f72ff',
                marginBottom: 16,
                borderBottom: '1px solid rgba(79,114,255,0.2)',
                paddingBottom: 8
              }}>
                {section.content}
              </h3>
            );
          case 'section':
            return (
              <h4 key={section.key} style={{
                fontSize: 16,
                fontWeight: 600,
                color: '#e8ecf4',
                marginTop: 20,
                marginBottom: 12
              }}>
                {section.content}
              </h4>
            );
          case 'risk-item':
            const isHigh = section.label.includes('High Risk');
            const isMedium = section.label.includes('Medium Risk');
            const isLow = section.label.includes('Low Risk');
            const color = isHigh ? '#ef4444' : isMedium ? '#f59e0b' : isLow ? '#22c55e' : '#64748b';
            return (
              <div key={section.key} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                marginBottom: 4,
                background: 'rgba(255,255,255,0.02)',
                borderRadius: 6,
                border: `1px solid ${color}20`
              }}>
                <span style={{ color, fontWeight: 500 }}>{section.label}</span>
                <span style={{ color: '#94a3b8', fontSize: 14 }}>{section.value}</span>
              </div>
            );
          case 'bold-item':
            return (
              <div key={section.key} style={{
                fontWeight: 600,
                color: '#e8ecf4',
                marginBottom: 8,
                paddingLeft: 16
              }}>
                • {section.content}
              </div>
            );
          case 'list-item':
            return (
              <div key={section.key} style={{
                color: '#cbd5e1',
                marginBottom: 6,
                paddingLeft: 16,
                lineHeight: 1.5
              }}>
                • {section.content}
              </div>
            );
          case 'numbered-item':
            return (
              <div key={section.key} style={{
                color: '#cbd5e1',
                marginBottom: 4,
                paddingLeft: 32,
                fontSize: 14,
                lineHeight: 1.4
              }}>
                {section.content}
              </div>
            );
          case 'indented':
            return (
              <div key={section.key} style={{
                color: '#94a3b8',
                marginBottom: 2,
                paddingLeft: 48,
                fontSize: 13,
                fontStyle: 'italic'
              }}>
                {section.content}
              </div>
            );
          case 'paragraph':
            return (
              <p key={section.key} style={{
                color: '#cbd5e1',
                marginBottom: 12,
                lineHeight: 1.6
              }}>
                {section.content}
              </p>
            );
          default:
            return null;
        }
      })}
    </div>
  );
}

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading]           = useState(false);
  const [results, setResults]           = useState(null);
  const [error, setError]               = useState(null);
  const [summary, setSummary]           = useState(null);
  const [summarizing, setSummarizing]   = useState(false);
  const [serviceHealth, setServiceHealth] = useState({
    status: 'unknown',
    model_server: 'unknown',
  });
  const [activeTab, setActiveTab] = useState('results');
  const [chatSessionId, setChatSessionId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    let active = true;

    const fetchHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        if (!response.ok) {
          throw new Error('Health endpoint unavailable');
        }
        const data = await response.json();
        if (active) {
          setServiceHealth({
            status: data.status || 'unknown',
            model_server: data.model_server || 'unknown',
          });
        }
      } catch {
        if (active) {
          setServiceHealth({ status: 'offline', model_server: 'offline' });
        }
      }
    };

    fetchHealth();
    const timer = setInterval(fetchHealth, 10000);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError(null);
    setResults(null);
    setSummary(null);
    setChatSessionId(null);
    setChatMessages([]);
    setActiveTab('results');
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setResults(null);
    setSummary(null); // Reset summary when re-analyzing

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
      setChatSessionId(data.session_id || null);
      setChatMessages([]);
      setActiveTab('results');
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(
        err.message || 'Failed to analyze contract. Please check if the backend server is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSummarize = async () => {
    if (!selectedFile) return;

    setSummarizing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://localhost:8000/summarize', {
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
      setSummary(data.summary);
    } catch (err) {
      console.error('Summarization failed:', err);
      setError(
        err.message || 'Failed to generate summary. Please check if the backend server is running.'
      );
    } finally {
      setSummarizing(false);
    }
  };

  const handleChatSend = async (question) => {
    if (!chatSessionId || !question?.trim()) {
      setError('Chat session is not ready yet. Upload and analyze the contract first, then open the Chat tab.');
      return;
    }

    const userMessage = { role: 'user', content: question, citations: [] };
    setChatMessages((prev) => [...prev, userMessage]);
    setChatLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: chatSessionId, question }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Chat error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setChatMessages(data.history || []);
    } catch (err) {
      console.error('Chat failed:', err);
      setError(err.message || 'Failed to get chat response.');
    } finally {
      setChatLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResults(null);
    setSummary(null);
    setError(null);
    setChatSessionId(null);
    setChatMessages([]);
    setChatLoading(false);
    setActiveTab('results');
  };

  return (
    <div style={{ minHeight: '100vh', padding: '0 16px 48px' }}>
      <div style={{ maxWidth: 820, margin: '0 auto' }}>
        {/* Hero header */}
        <Header />

        {/* Service health badge */}
        <div style={{
          marginBottom: 14,
          display: 'flex',
          justifyContent: 'center',
        }}>
          <span style={{
            fontSize: 12,
            fontWeight: 600,
            padding: '6px 12px',
            borderRadius: 999,
            border: serviceHealth.model_server === 'ready'
              ? '1px solid rgba(34,197,94,0.4)'
              : serviceHealth.model_server === 'offline'
                ? '1px solid rgba(239,68,68,0.4)'
                : '1px solid rgba(148,163,184,0.4)',
            background: serviceHealth.model_server === 'ready'
              ? 'rgba(34,197,94,0.12)'
              : serviceHealth.model_server === 'offline'
                ? 'rgba(239,68,68,0.12)'
                : 'rgba(148,163,184,0.12)',
            color: serviceHealth.model_server === 'ready'
              ? '#22c55e'
              : serviceHealth.model_server === 'offline'
                ? '#ef4444'
                : '#94a3b8',
          }}>
            Model: {
              serviceHealth.model_server === 'ready'
                ? 'Online'
                : serviceHealth.model_server === 'disabled'
                  ? 'Disabled'
                  : serviceHealth.model_server === 'offline'
                    ? 'Offline (Pinecone fallback)'
                    : 'Starting'
            }
          </span>
        </div>

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
              <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                <button
                  onClick={() => setActiveTab('results')}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 99,
                    border: activeTab === 'results' ? '1px solid #4f72ff' : '1px solid rgba(255,255,255,0.12)',
                    background: activeTab === 'results' ? 'rgba(79,114,255,0.14)' : 'transparent',
                    color: activeTab === 'results' ? '#93c5fd' : '#94a3b8',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Results
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 99,
                    border: activeTab === 'chat' ? '1px solid #4f72ff' : '1px solid rgba(255,255,255,0.12)',
                    background: activeTab === 'chat' ? 'rgba(79,114,255,0.14)' : 'transparent',
                    color: activeTab === 'chat' ? '#93c5fd' : '#94a3b8',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Chat
                </button>
              </div>

              {activeTab === 'results' && (
                <>
                  <ResultsList results={results} />

                  {/* Summary Section */}
                  <div style={{ marginTop: 32 }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: 20,
                    }}>
                      <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e8ecf4' }}>
                        Document Summary
                      </h2>
                      {!summary && !summarizing && (
                        <button
                          className="btn-primary"
                          onClick={handleSummarize}
                          disabled={summarizing}
                          style={{ fontSize: 14, padding: '8px 16px' }}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ marginRight: 8 }}>
                            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5.586a1 1 0 0 1 .707.293l5.414 5.414a1 1 0 0 1 .293.707V19a2 2 0 0 1-2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                          Generate Summary
                        </button>
                      )}
                    </div>

                    {/* Summarizing indicator */}
                    {summarizing && (
                      <div style={{
                        textAlign: 'center',
                        padding: '40px 0',
                        color: '#64748b',
                      }}>
                        <div style={{
                          width: 24,
                          height: 24,
                          border: '2px solid #4f72ff',
                          borderTop: '2px solid transparent',
                          borderRadius: '50%',
                          animation: 'spin 1s linear infinite',
                          margin: '0 auto 16px',
                        }} />
                        Generating summary...
                      </div>
                    )}

                    {/* Summary content */}
                    {summary && !summarizing && (
                      <div style={{
                        background: 'rgba(17,24,39,0.6)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: 12,
                        padding: '24px',
                        color: '#e8ecf4',
                      }}>
                        <SummaryDisplay summary={summary} />
                      </div>
                    )}
                  </div>
                </>
              )}

              {activeTab === 'chat' && (
                <ChatPanel
                  sessionId={chatSessionId}
                  messages={chatMessages}
                  loading={chatLoading}
                  disabled={!chatSessionId}
                  onSend={handleChatSend}
                />
              )}

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
