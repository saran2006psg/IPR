import React from 'react';
import { cleanDisplayText } from '../utils/textSanitizer';

function formatDate(epochSeconds) {
  if (!epochSeconds) {
    return 'Unknown time';
  }
  const dt = new Date(epochSeconds * 1000);
  if (Number.isNaN(dt.getTime())) {
    return 'Unknown time';
  }
  return dt.toLocaleString();
}

export default function HistoryView({
  sessions = [],
  loading = false,
  error = '',
  onRefresh,
  onOpenSession,
}) {
  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-title)', margin: 0 }}>Session History</h2>
          <p style={{ margin: '6px 0 0', color: 'var(--text-muted)', fontSize: 14 }}>
            Reopen previous contract analyses and continue the chat.
          </p>
        </div>
        <button className="btn-outline" onClick={onRefresh} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error ? (
        <div style={{ marginBottom: 14, padding: '10px 12px', borderRadius: 8, border: '1px solid #fecaca', background: '#fef2f2', color: '#991b1b', fontSize: 13 }}>
          {error}
        </div>
      ) : null}

      {loading && sessions.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '30px 10px' }}>Loading history...</div>
      ) : null}

      {!loading && sessions.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px 10px' }}>
          No previous sessions found yet. Analyze a contract first.
        </div>
      ) : null}

      <div style={{ display: 'grid', gap: 12 }}>
        {sessions.map((session) => (
          <div
            key={session.session_id}
            style={{
              border: '1px solid var(--border-light)',
              borderRadius: 10,
              background: '#fff',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 16,
            }}
          >
            <div style={{ minWidth: 0 }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--text-title)' }}>
                {cleanDisplayText(session.file_name || 'uploaded_contract.pdf')}
              </h3>
              <p style={{ margin: '6px 0 0', fontSize: 13, color: 'var(--text-body)' }}>
                {session.clause_count || 0} clauses - {session.high_risk_count || 0} high-risk
              </p>
              <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>
                {cleanDisplayText(session.agreement_type || 'Agreement unknown')} - {cleanDisplayText(session.user_type || 'Role unknown')}
              </p>
              <p style={{ margin: '6px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>
                Last updated: {formatDate(session.updated_at)}
              </p>
            </div>
            <button
              className="btn-primary"
              onClick={() => onOpenSession?.(session.session_id)}
              disabled={loading}
              style={{ whiteSpace: 'nowrap' }}
            >
              Open Session
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
