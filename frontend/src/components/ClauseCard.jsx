import React, { useState } from 'react';

function riskStyle(level) {
  switch (level) {
    case 'HIGH':   return { badge: 'badge badge-high',   border: '#ef4444', dot: '#ef4444', label: '🔴 HIGH' };
    case 'MEDIUM': return { badge: 'badge badge-medium', border: '#f59e0b', dot: '#f59e0b', label: '🟡 MEDIUM' };
    case 'LOW':    return { badge: 'badge badge-low',    border: '#22c55e', dot: '#22c55e', label: '🟢 LOW' };
    default:       return { badge: 'badge badge-unknown',border: '#64748b', dot: '#64748b', label: '⚪ UNKNOWN' };
  }
}

function ScoreBar({ score }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.85 ? '#ef4444' : score >= 0.70 ? '#f59e0b' : '#22c55e';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
      <div style={{
        flex: 1, height: 4, borderRadius: 99,
        background: 'rgba(255,255,255,0.06)',
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: color,
          borderRadius: 99,
          transition: 'width 0.6s ease',
        }} />
      </div>
      <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: "'JetBrains Mono', monospace", minWidth: 32 }}>
        {pct}%
      </span>
    </div>
  );
}

function ClauseCard({ result, index }) {
  const [open, setOpen] = useState(false);
  const { clause, risk_level, explanation, similar_clauses = [] } = result;
  const s = riskStyle(risk_level);
  const hasSimilar = similar_clauses.length > 0;

  return (
    <div
      className="animate-slide-up"
      style={{
        borderRadius: 12,
        border: `1px solid rgba(255,255,255,0.06)`,
        borderLeft: `3px solid ${s.border}`,
        background: 'rgba(26,34,54,0.7)',
        marginBottom: 12,
        overflow: 'hidden',
        transition: 'box-shadow 0.2s',
        animationDelay: `${index * 50}ms`,
      }}
    >
      {/* Card header */}
      <div style={{ padding: '16px 20px' }}>
        {/* Top row: badge + clause number */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 12,
          flexWrap: 'wrap',
          gap: 8,
        }}>
          <span className={s.badge}>{s.label} RISK</span>
          <span style={{
            fontSize: 11,
            color: '#475569',
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            CLAUSE #{String(index + 1).padStart(2, '0')}
          </span>
        </div>

        {/* Clause text */}
        <div style={{
          background: 'rgba(0,0,0,0.25)',
          border: '1px solid rgba(255,255,255,0.05)',
          borderRadius: 8,
          padding: '12px 14px',
          marginBottom: 12,
        }}>
          <p style={{
            color: '#cbd5e1',
            fontSize: 13,
            lineHeight: 1.65,
            fontFamily: 'Inter, sans-serif',
          }}>
            {clause.length > 400 ? clause.slice(0, 400) + '…' : clause}
          </p>
        </div>

        {/* Explanation */}
        <div>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#475569',
            textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
            Risk Analysis
          </p>
          <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.65 }}>
            {explanation || 'No further details available.'}
          </p>
        </div>
      </div>

      {/* Similar clauses toggle */}
      {hasSimilar && (
        <div>
          <button
            onClick={() => setOpen(!open)}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 20px',
              background: 'rgba(79,114,255,0.06)',
              border: 'none',
              borderTop: '1px solid rgba(255,255,255,0.05)',
              color: '#7c9dff',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              fontFamily: 'Inter, sans-serif',
              letterSpacing: '0.04em',
            }}
          >
            <span>
              🔍 {similar_clauses.length} similar clause{similar_clauses.length > 1 ? 's' : ''} in knowledge base
            </span>
            <svg
              width="14" height="14" viewBox="0 0 24 24" fill="none"
              style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
            >
              <path d="m6 9 6 6 6-6" stroke="#7c9dff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>

          {open && (
            <div style={{ padding: '12px 20px 16px', background: 'rgba(0,0,0,0.18)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {similar_clauses.slice(0, 5).map((sc, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 10,
                    padding: '10px 12px',
                    borderRadius: 8,
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}>
                    {/* severity dot */}
                    <span style={{
                      width: 7, height: 7,
                      borderRadius: '50%',
                      background: riskStyle(sc.severity).dot,
                      flexShrink: 0,
                      marginTop: 5,
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        marginBottom: 4,
                        flexWrap: 'wrap',
                      }}>
                        <span style={{
                          fontSize: 10,
                          fontWeight: 700,
                          color: riskStyle(sc.severity).dot,
                          textTransform: 'uppercase',
                          letterSpacing: '0.06em',
                        }}>{sc.severity}</span>
                        <span style={{
                          fontSize: 10, color: '#475569',
                          fontFamily: "'JetBrains Mono', monospace",
                          background: 'rgba(255,255,255,0.05)',
                          padding: '1px 6px', borderRadius: 4,
                        }}>{sc.clause_type}</span>
                        <ScoreBar score={sc.score} />
                      </div>
                      <p style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>
                        {sc.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ClauseCard;
