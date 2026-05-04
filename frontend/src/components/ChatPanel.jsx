import React, { useRef, useEffect, useState } from 'react';
import { cleanDisplayText } from '../utils/textSanitizer';

const QUICK_PROMPTS = [
  'Explain this clause in simple terms',
  'What is my biggest legal risk here?',
  'Suggest safer wording for this clause',
];

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

  const handleQuickPrompt = (prompt) => {
    if (loading) return;
    onSend(prompt);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div ref={listRef} style={{ flex: 1, overflowY: 'auto', paddingBottom: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {sessionId ? (
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Session active
          </div>
        ) : null}

        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)', fontSize: 14 }}>
            <div style={{ width: 40, height: 40, background: 'var(--bg-main)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z"/></svg>
            </div>
            Ask questions about the selected clause or whole contract.
            <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  className="btn-outline"
                  onClick={() => handleQuickPrompt(prompt)}
                  style={{ fontSize: 12, padding: '6px 10px' }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, idx) => {
            const isUser = m.role === 'user';
            const content = isUser
              ? cleanDisplayText(m.content)
              : cleanDisplayText(softenRiskLabels(m.content));
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

      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-light)', paddingTop: 14 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleSend(); }}
            placeholder="Ask for risk detail, rewrite suggestions, or negotiation strategy..."
            style={{ 
              flex: 1,
              padding: '10px 14px',
              borderRadius: 8,
              border: '1px solid var(--border-strong)', 
              fontSize: 14,
              outline: 'none',
              background: '#ffffff',
            }}
          />
          <button className="btn-primary" onClick={handleSend} disabled={loading || !draft.trim()} style={{ padding: '8px 12px', minWidth: 72 }}>
            Send
          </button>
        </div>
      </div>
      <style>{`@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }`}</style>
    </div>
  );
}
