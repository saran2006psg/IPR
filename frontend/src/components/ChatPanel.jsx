import React, { useRef, useEffect, useState } from 'react';

function softenRiskLabels(text = '') {
  return text
    .replace(/\bHIGH\b/g, 'CAREFUL')
    .replace(/\bMEDIUM\b/g, 'REVIEW')
    .replace(/\bLOW\b/g, 'STANDARD')
    .replace(/\bHigh\b/g, 'Careful')
    .replace(/\bMedium\b/g, 'Review')
    .replace(/\bLow\b/g, 'Standard')
    .replace(/\bhigh\b/g, 'careful')
    .replace(/\bmedium\b/g, 'review')
    .replace(/\blow\b/g, 'standard');
}

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
            const content = isUser ? m.content : softenRiskLabels(m.content);
            return (
              <div key={idx} style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
                <div style={{
                  maxWidth: '90%', padding: '10px 14px', borderRadius: 8, fontSize: 14, lineHeight: 1.5,
                  background: isUser ? '#111827' : '#f3f4f6',
                  color: isUser ? '#ffffff' : 'var(--text-body)',
                  border: isUser ? 'none' : '1px solid var(--border-light)'
                }}>
                  {content}
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
