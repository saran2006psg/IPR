import os

css_content = """@import "tailwindcss";

:root {
  --bg-main: #f9fafb;
  --bg-panel: #ffffff;
  --bg-sidebar: #f3f4f6;
  
  --border-light: #e5e7eb;
  --border-strong: #d1d5db;

  --text-title: #111827;
  --text-body: #374151;
  --text-muted: #6b7280;

  --accent: #0f172a;
  --accent-hover: #1e293b;

  --risk-high: #dc2626;
  --risk-high-bg: #fef2f2;
  --risk-high-border: #fca5a5;

  --risk-med: #d97706;
  --risk-med-bg: #fffbeb;
  --risk-med-border: #fcd34d;

  --risk-low: #059669;
  --risk-low-bg: #ecfdf5;
  --risk-low-border: #6ee7b7;
}

*, *::before, *::after { box-sizing: border-box; }

body {
  background-color: var(--bg-main);
  color: var(--text-body);
  font-family: 'Inter', -apple-system, sans-serif;
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

.btn-primary {
  background-color: #111827;
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
  cursor: pointer;
  border: 1px solid transparent;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-primary:hover:not(:disabled) { background-color: #374151; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-outline {
  background-color: #ffffff;
  color: #374151;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
  cursor: pointer;
  border: 1px solid #d1d5db;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-outline:hover:not(:disabled) { background-color: #f9fafb; }

.card {
  background-color: var(--bg-panel);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
"""

with open("d:\\roberta-base\\frontend\\src\\index.css", "w", encoding="utf-8") as f:
    f.write(css_content)

sidebar_jsx = """import React from 'react';

export default function Sidebar({ currentView, setView }) {
  const navItems = [
    { id: 'dashboard', icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z', label: 'Dashboard' },
    { id: 'upload', icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12', label: 'Upload Contract' },
    { id: 'analysis', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', label: 'Risk Analysis' },
    { id: 'history', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', label: 'History' }
  ];

  return (
    <div style={{
      width: 240,
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-light)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      flexShrink: 0
    }}>
      <div style={{ padding: '20px 20px 12px' }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-title)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 24, height: 24, background: '#111827', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </div>
          LexGuard
        </h1>
      </div>
      
      <div style={{ padding: '0 20px', marginBottom: 20 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Enterprise Scanner</span>
      </div>

      <nav style={{ padding: '0 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setView(item.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 10, width: '100%',
              padding: '8px 12px', borderRadius: 6,
              background: currentView === item.id ? '#e5e7eb' : 'transparent',
              color: currentView === item.id ? '#111827' : 'var(--text-muted)',
              fontWeight: currentView === item.id ? 600 : 500,
              fontSize: 14, border: 'none', cursor: 'pointer', textAlign: 'left',
              transition: 'all 0.15s'
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d={item.icon} />
            </svg>
            {item.label}
          </button>
        ))}
      </nav>

      <div style={{ padding: '20px 16px', borderTop: '1px solid var(--border-light)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #d1d5db, #9ca3af)' }}></div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-title)' }}>Jane Doe</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Legal Dept</div>
          </div>
        </div>
      </div>
    </div>
  );
}
"""
with open("d:\\roberta-base\\frontend\\src\\components\\Sidebar.jsx", "w", encoding="utf-8") as f:
    f.write(sidebar_jsx)

dashboard_jsx = """import React from 'react';

export default function Dashboard({ onUploadClick }) {
  return (
    <div style={{ padding: '40px 48px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
      <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-title)', marginBottom: 32 }}>System Overview</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr)', gap: 24, marginBottom: 40 }}>
        <div className="card" style={{ padding: 24 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.05em' }}>Contracts Analyzed</div>
          <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--text-title)' }}>148</div>
        </div>
        <div className="card" style={{ padding: 24 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.05em' }}>Avg. Exposure Score</div>
          <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--text-title)' }}>34/100</div>
        </div>
        <div className="card" style={{ padding: 24, borderTop: '4px solid var(--risk-high)' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', marginBottom: 8, letterSpacing: '0.05em' }}>Action Required</div>
          <div style={{ fontSize: 36, fontWeight: 700, color: 'var(--risk-high)' }}>12</div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-title)' }}>Recent Activity</h2>
        <button className="btn-primary" onClick={onUploadClick}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14"/></svg>
          New Analysis
        </button>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#f9fafb', borderBottom: '1px solid var(--border-light)' }}>
              <th style={{ padding: '14px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Document Name</th>
              <th style={{ padding: '14px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Analyzed On</th>
              <th style={{ padding: '14px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Status</th>
              <th style={{ padding: '14px 24px', fontWeight: 500, color: 'var(--text-muted)' }}>Risk Exposure</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
              <td style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-title)' }}>Enterprise_MSA_Template_v3.pdf</td>
              <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>Today, 10:42 AM</td>
              <td style={{ padding: '16px 24px' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, background: 'var(--risk-low-bg)', color: 'var(--risk-low)', padding: '2px 8px', borderRadius: 12, fontWeight: 500 }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }}/> Complete
                </span>
              </td>
              <td style={{ padding: '16px 24px', fontWeight: 600, color: 'var(--risk-high)' }}>High (82/100)</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
              <td style={{ padding: '16px 24px', fontWeight: 500, color: 'var(--text-title)' }}>AcmeCorp_NDA_Signed.pdf</td>
              <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>Yesterday</td>
              <td style={{ padding: '16px 24px' }}>
                 <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, background: 'var(--risk-low-bg)', color: 'var(--risk-low)', padding: '2px 8px', borderRadius: 12, fontWeight: 500 }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }}/> Complete
                </span>
              </td>
              <td style={{ padding: '16px 24px', fontWeight: 600, color: 'var(--risk-low)' }}>Low (14/100)</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
"""
with open("d:\\roberta-base\\frontend\\src\\components\\Dashboard.jsx", "w", encoding="utf-8") as f:
    f.write(dashboard_jsx)


upload_view_jsx = """import React, { useCallback, useState } from 'react';

export default function UploadView({ onFileSelect, selectedFile, onAnalyze, loading }) {
  const [dragging, setDragging] = useState(false);

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
        <div className="card" style={{ padding: '60px 40px', textAlign: 'center' }}>
          <div style={{
            width: 48, height: 48, border: '3px solid var(--border-light)', 
            borderTopColor: 'var(--accent)', borderRadius: '50%', 
            animation: 'spin 1s linear infinite', margin: '0 auto 24px'
          }} />
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-title)' }}>Analyzing Document...</h3>
          <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>Extracting clauses and querying legal precedence database.</p>
        </div>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
"""
with open("d:\\roberta-base\\frontend\\src\\components\\UploadView.jsx", "w", encoding="utf-8") as f:
    f.write(upload_view_jsx)


chat_panel_jsx = """import React, { useRef, useEffect, useState } from 'react';

export default function ChatPanel({ sessionId, messages, loading, onSend }) {
  const [draft, setDraft] = useState('');
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSend = () => {
    if (!draft.trim() || loading) return;
    onSend(draft.trim());
    setDraft('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div ref={listRef} style={{ flex: 1, overflowY: 'auto', paddingBottom: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)', fontSize: 14 }}>
            <div style={{ width: 40, height: 40, background: 'var(--bg-main)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z"/></svg>
            </div>
            Ask questions about this specific clause or the entire contract. <br/>
            Try: <br/><br/>
            <button className="btn-outline" onClick={() => onSend('Explain this clause in simple terms')}>"Explain this clause in simple terms"</button>
          </div>
        ) : (
          messages.map((m, idx) => {
            const isUser = m.role === 'user';
            return (
              <div key={idx} style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
                <div style={{
                  maxWidth: '90%', padding: '10px 14px', borderRadius: 8, fontSize: 14, lineHeight: 1.5,
                  background: isUser ? '#111827' : '#f3f4f6',
                  color: isUser ? '#ffffff' : 'var(--text-body)',
                  border: isUser ? 'none' : '1px solid var(--border-light)'
                }}>
                  {m.content}
                </div>
              </div>
            );
          })
        )}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '10px 14px', borderRadius: 8, background: '#f3f4f6', border: '1px solid var(--border-light)', display: 'flex', gap: 4, alignItems: 'center' }}>
              <div style={{ width: 6, height: 6, background: '#9ca3af', borderRadius: '50%', animation: 'pulse 1.5s infinite' }} />
              <div style={{ width: 6, height: 6, background: '#9ca3af', borderRadius: '50%', animation: 'pulse 1.5s infinite 0.2s' }} />
              <div style={{ width: 6, height: 6, background: '#9ca3af', borderRadius: '50%', animation: 'pulse 1.5s infinite 0.4s' }} />
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-light)', paddingTop: 16 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleSend(); }}
            placeholder="Ask the AI assistant..."
            style={{ 
              flex: 1, padding: '10px 14px', borderRadius: 6, border: '1px solid var(--border-strong)', 
              fontSize: 14, outline: 'none' 
            }}
          />
          <button className="btn-primary" onClick={handleSend} disabled={loading || !draft.trim()} style={{ padding: '8px 12px' }}>
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
          </button>
        </div>
      </div>
      <style>{`@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }`}</style>
    </div>
  );
}
"""
with open("d:\\roberta-base\\frontend\\src\\components\\ChatPanel.jsx", "w", encoding="utf-8") as f:
    f.write(chat_panel_jsx)

analysis_view_jsx = """import React, { useState } from 'react';
import ChatPanel from './ChatPanel';

function getRiskToken(level) {
  switch (level) {
    case 'HIGH':   return { bg: 'var(--risk-high-bg)', color: 'var(--risk-high)', border: 'var(--risk-high-border)', label: 'High' };
    case 'MEDIUM': return { bg: 'var(--risk-med-bg)', color: 'var(--risk-med)', border: 'var(--risk-med-border)', label: 'Medium' };
    case 'LOW':    return { bg: 'var(--risk-low-bg)', color: 'var(--risk-low)', border: 'var(--risk-low-border)', label: 'Low' };
    default:       return { bg: '#f3f4f6', color: '#4b5563', border: '#d1d5db', label: 'Unknown' };
  }
}

export default function AnalysisView({ results = [], chatSessionId, chatMessages, onChatSend, chatLoading }) {
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (!results || results.length === 0) return null;

  const selected = results[selectedIdx];
  const risk = getRiskToken(selected?.risk_level);
  const highCount = results.filter(r => r.risk_level === 'HIGH').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0' }}>
      
      {/* Top Banner Context */}
      <div style={{ padding: '24px 32px', background: '#fff', borderBottom: '1px solid var(--border-light)' }}>
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-title)' }}>Contract Analysis</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{results.length} clauses parsed &middot; {highCount} critical issues found</p>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button className="btn-outline">Export PDF</button>
              <button className="btn-primary">Resolve Tasks</button>
            </div>
         </div>
      </div>

      {/* Main Split Interface */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
        
        {/* Left pane: Clauses List */}
        <div style={{ flex: '1', borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', background: 'var(--bg-main)' }}>
          <div style={{ padding: '16px 24px', fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Document Flow
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
             {results.map((r, i) => {
               const st = getRiskToken(r.risk_level);
               const isSel = selectedIdx === i;
               return (
                 <div
                   key={i}
                   onClick={() => setSelectedIdx(i)}
                   style={{
                     padding: 16, background: isSel ? '#fff' : 'transparent',
                     border: `1px solid ${isSel ? 'var(--border-strong)' : 'transparent'}`,
                     borderRadius: 8, cursor: 'pointer',
                     boxShadow: isSel ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
                     borderLeft: `4px solid ${isSel ? st.color : 'transparent'}`,
                     transition: 'all 0.1s'
                   }}
                 >
                   <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, alignItems: 'center' }}>
                     <span style={{ fontSize: 13, fontWeight: 600, color: isSel ? 'var(--text-title)' : 'var(--text-muted)' }}>Clause {i + 1}</span>
                     {r.risk_level !== 'LOW' && (
                       <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 12, background: st.bg, color: st.color }}>
                         {st.label}
                       </span>
                     )}
                   </div>
                   <div style={{ 
                     fontSize: 14, color: 'var(--text-body)', lineHeight: 1.6,
                     display: '-webkit-box', WebkitLineClamp: isSel ? 'none' : '2', WebkitBoxOrient: 'vertical', overflow: 'hidden'
                   }}>
                     {r.clause}
                   </div>
                 </div>
               );
             })}
          </div>
        </div>

        {/* Right pane: Insight & Chat */}
        <div style={{ width: 480, display: 'flex', flexDirection: 'column', background: '#fff' }}>
          
          {/* Selected Insights Top */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 24, borderBottom: '1px solid var(--border-light)' }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
               <span style={{ fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 4, background: risk.bg, color: risk.color, border: `1px solid ${risk.border}` }}>
                 {risk.label} Exposure
               </span>
             </div>
             
             <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-title)', marginBottom: 8 }}>Risk Explanation</h3>
             <p style={{ fontSize: 14, color: 'var(--text-body)', lineHeight: 1.5, marginBottom: 24 }}>
               {selected?.explanation || 'This clause operates on standardized terms with low legal exposure.'}
             </p>

             {selected?.similar_clauses?.length > 0 && (
               <div>
                 <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-title)', marginBottom: 8 }}>Precedence Matches</h3>
                 <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                   {selected.similar_clauses.slice(0, 2).map((sc, i) => (
                     <div key={i} style={{ padding: 12, background: 'var(--bg-main)', border: `1px solid var(--border-light)`, borderRadius: 6 }}>
                       <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>Match from: {sc.document || sc.clause_type}</div>
                       <div style={{ fontSize: 13, color: 'var(--text-body)', lineHeight: 1.4 }}>"{sc.text}"</div>
                     </div>
                   ))}
                 </div>
               </div>
             )}
          </div>

          {/* Chat Panel Bottom */}
          <div style={{ height: 400, display: 'flex', flexDirection: 'column', padding: 24, background: '#f9fafb' }}>
             <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-title)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                AI Assistant
             </h3>
             <div style={{ flex: 1, minHeight: 0 }}>
               <ChatPanel 
                 sessionId={chatSessionId}
                 messages={chatMessages}
                 loading={chatLoading}
                 onSend={onChatSend}
               />
             </div>
          </div>

        </div>

      </div>
    </div>
  );
}
"""
with open("d:\\roberta-base\\frontend\\src\\components\\AnalysisView.jsx", "w", encoding="utf-8") as f:
    f.write(analysis_view_jsx)


app_jsx = """import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import UploadView from './components/UploadView';
import AnalysisView from './components/AnalysisView';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  
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
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Sidebar currentView={currentView} setView={setCurrentView} />
      
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        {currentView === 'dashboard' && <Dashboard onUploadClick={() => setCurrentView('upload')} />}
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
"""
with open("d:\\roberta-base\\frontend\\src\\App.jsx", "w", encoding="utf-8") as f:
    f.write(app_jsx)

print("Enterprise redesign complete!")
