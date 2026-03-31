import { useEffect, useRef, useState } from 'react';

const QUICK_ACTIONS = [
  'Give me a short summary of this contract',
  'What are the highest risk clauses?',
  'What are termination conditions?',
  'What obligations does the employee have?'
];

function CitationList({ citations = [] }) {
  if (!citations.length) return null;

  return (
    <div style={{ marginTop: 8 }}>
      <p style={{ color: '#94a3b8', fontSize: 11, marginBottom: 6 }}>Sources</p>
      {citations.slice(0, 3).map((c, idx) => (
        <div key={`${c.clause_index}-${idx}`} style={{
          border: '1px solid rgba(79,114,255,0.25)',
          background: 'rgba(79,114,255,0.08)',
          borderRadius: 8,
          padding: '8px 10px',
          marginBottom: 6,
        }}>
          <div style={{ color: '#93c5fd', fontSize: 11, marginBottom: 2 }}>
            Context #{(c.clause_index ?? 0) + 1} · {c.risk_level} · score {c.relevance_score}
          </div>
          <div style={{ color: '#cbd5e1', fontSize: 12, lineHeight: 1.4 }}>{c.snippet}</div>
        </div>
      ))}
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  
  // PHASE 1: Determine quality indicator based on confidence and quality score
  const getQualityIndicator = (confidence, quality) => {
    if (quality !== undefined && quality >= 0.7) return { icon: '🟢', label: 'High confidence', color: '#22c55e' };
    if (quality !== undefined && quality >= 0.4) return { icon: '🟡', label: 'Medium confidence', color: '#f59e0b' };
    if (quality !== undefined) return { icon: '🔴', label: 'Low confidence', color: '#ef4444' };
    if (confidence >= 0.5) return { icon: '🟢', label: 'High confidence', color: '#22c55e' };
    if (confidence >= 0) return { icon: '🟡', label: 'Medium confidence', color: '#f59e0b' };
    return { icon: '🔴', label: 'Low confidence', color: '#ef4444' };
  };
  
  const quality = getQualityIndicator(message.confidence, message.quality);
  
  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 12,
    }}>
      <div style={{
        maxWidth: '86%',
        borderRadius: 12,
        padding: '10px 12px',
        border: isUser ? '1px solid rgba(79,114,255,0.45)' : '1px solid rgba(255,255,255,0.1)',
        background: isUser ? 'rgba(79,114,255,0.16)' : 'rgba(17,24,39,0.7)',
      }}>
        <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.5 }}>{message.content}</div>
        {!isUser && (
          <div style={{ marginTop: 6, fontSize: 11, color: '#94a3b8', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <span>{quality.icon} {quality.label}</span>
            {message.quality !== undefined && (
              <span>Quality: {(message.quality * 100).toFixed(0)}%</span>
            )}
            {message.confidence !== undefined && message.quality === undefined && (
              <span>Score: {message.confidence.toFixed(2)}</span>
            )}
            {message.fallback_used && <span>⚠️ fallback</span>}
          </div>
        )}
        {!isUser && <CitationList citations={message.citations || []} />}
      </div>
    </div>
  );
}

export default function ChatPanel({
  sessionId,
  messages,
  loading,
  disabled,
  onSend,
}) {
  const [draft, setDraft] = useState('');
  const listRef = useRef(null);

  useEffect(() => {
    if (!listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, loading]);

  const send = () => {
    const q = draft.trim();
    if (!q || loading || disabled) return;
    onSend(q);
    setDraft('');
  };

  return (
    <div style={{ marginTop: 18 }}>
      <div style={{
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 12,
        background: 'rgba(2,6,23,0.45)',
        padding: 14,
      }}>
        <div style={{ marginBottom: 10, color: '#94a3b8', fontSize: 12, display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
          Session: {sessionId ? `${sessionId.slice(0, 8)}...` : 'Not initialized'}
          <span style={{ color: disabled ? '#f59e0b' : '#22c55e' }}>
            {disabled ? 'Chat unavailable until analysis completes' : 'Chat ready'}
          </span>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
          {QUICK_ACTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => {
                if (!disabled && !loading) onSend(q);
              }}
              disabled={disabled || loading}
              style={{
                borderRadius: 999,
                border: '1px solid rgba(79,114,255,0.3)',
                background: 'rgba(79,114,255,0.12)',
                color: '#bfdbfe',
                padding: '6px 12px',
                fontSize: 12,
                cursor: disabled || loading ? 'not-allowed' : 'pointer',        
                opacity: disabled || loading ? 0.5 : 1,
                transition: 'all 0.2s',
              }}
              onMouseOver={(e) => {
                if (!disabled && !loading) {
                  e.target.style.background = 'rgba(79,114,255,0.25)';
                }
              }}
              onMouseOut={(e) => {
                if (!disabled && !loading) {
                  e.target.style.background = 'rgba(79,114,255,0.12)';
                }
              }}
            >
              {q}
            </button>
          ))}
        </div>

        <div ref={listRef} style={{
          minHeight: 260,
          maxHeight: 360,
          overflowY: 'auto',
          paddingRight: 4,
          marginBottom: 12,
        }}>
          {!messages.length && (
            <div style={{ color: '#64748b', fontSize: 13, textAlign: 'center', marginTop: 60 }}>
              Ask anything about this contract.
            </div>
          )}
          {messages.map((m, idx) => (
            <MessageBubble key={`${m.role}-${idx}`} message={m} />
          ))}
          {loading && (
            <div style={{ color: '#93c5fd', fontSize: 12 }}>Assistant is thinking...</div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            disabled={disabled || loading}
            placeholder="Ask a question about this contract... (Press Enter to send)"
            style={{
              flex: 1,
              borderRadius: 10,
              border: '1px solid rgba(255,255,255,0.15)',
              background: 'rgba(15,23,42,0.7)',
              color: '#e2e8f0',
              padding: '12px 14px',
              fontSize: 14,
              outline: 'none',
              transition: 'border 0.2s',
            }}
            onFocus={(e) => e.target.style.border = '1px solid rgba(79,114,255,0.6)'}
            onBlur={(e) => e.target.style.border = '1px solid rgba(255,255,255,0.15)'}
          />
          <button
            className="btn-primary"
            disabled={disabled || loading || !draft.trim()}
            onClick={send}
            style={{ 
              padding: '10px 18px', 
              fontSize: 14,
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            Send <span>&#10148;</span>
          </button>
        </div>
      </div>
    </div>
  );
}
