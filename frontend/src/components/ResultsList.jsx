import React, { useState } from 'react';
import ClauseCard from './ClauseCard';

const FILTER_TABS = ['ALL', 'HIGH', 'MEDIUM', 'LOW'];

function StatCard({ count, label, color, bg }) {
  return (
    <div style={{
      flex: '1 1 0',
      minWidth: 80,
      padding: '16px 12px',
      borderRadius: 10,
      background: bg,
      border: `1px solid ${color}44`,
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{count}</div>
      <div style={{ fontSize: 11, color, fontWeight: 600, marginTop: 4,
        textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
    </div>
  );
}

function ResultsList({ results }) {
  const [filter, setFilter] = useState('ALL');

  if (!results || results.length === 0) return null;

  const counts = results.reduce(
    (acc, r) => { acc[r.risk_level] = (acc[r.risk_level] || 0) + 1; return acc; },
    { HIGH: 0, MEDIUM: 0, LOW: 0, UNKNOWN: 0 }
  );

  const filtered = filter === 'ALL'
    ? results
    : results.filter((r) => r.risk_level === filter);

  return (
    <div className="animate-slide-up" style={{ marginTop: 32 }}>
      {/* ── Header row ── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20,
        flexWrap: 'wrap',
        gap: 10,
      }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e8ecf4' }}>
          Analysis Results
        </h2>
        <span style={{
          fontSize: 12, fontWeight: 600,
          color: '#4f72ff',
          background: 'rgba(79,114,255,0.1)',
          border: '1px solid rgba(79,114,255,0.25)',
          padding: '4px 12px', borderRadius: 99,
        }}>
          {results.length} clause{results.length !== 1 ? 's' : ''} analyzed
        </span>
      </div>

      {/* ── Risk summary cards ── */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 22 }}>
        <StatCard count={counts.HIGH}   label="High Risk"   color="#ef4444" bg="rgba(239,68,68,0.08)" />
        <StatCard count={counts.MEDIUM} label="Med Risk"    color="#f59e0b" bg="rgba(245,158,11,0.08)" />
        <StatCard count={counts.LOW}    label="Low Risk"    color="#22c55e" bg="rgba(34,197,94,0.08)" />
      </div>

      {/* ── Risk meter bar ── */}
      {results.length > 0 && (
        <div style={{ marginBottom: 22 }}>
          <div style={{
            display: 'flex',
            height: 6,
            borderRadius: 99,
            overflow: 'hidden',
            gap: 2,
          }}>
            {counts.HIGH > 0 && (
              <div style={{
                flex: counts.HIGH, background: '#ef4444',
                borderRadius: '99px 0 0 99px',
                transition: 'flex 0.4s ease',
              }} />
            )}
            {counts.MEDIUM > 0 && (
              <div style={{
                flex: counts.MEDIUM, background: '#f59e0b',
                transition: 'flex 0.4s ease',
              }} />
            )}
            {counts.LOW > 0 && (
              <div style={{
                flex: counts.LOW, background: '#22c55e',
                borderRadius: '0 99px 99px 0',
                transition: 'flex 0.4s ease',
              }} />
            )}
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            marginTop: 5, fontSize: 10, color: '#475569',
          }}>
            <span>Overall risk distribution</span>
            <span>
              {counts.HIGH > 0 ? `${Math.round(counts.HIGH / results.length * 100)}% high · ` : ''}
              {counts.MEDIUM > 0 ? `${Math.round(counts.MEDIUM / results.length * 100)}% medium · ` : ''}
              {counts.LOW > 0 ? `${Math.round(counts.LOW / results.length * 100)}% low` : ''}
            </span>
          </div>
        </div>
      )}

      {/* ── Filter tabs ── */}
      <div style={{
        display: 'flex',
        gap: 6,
        marginBottom: 16,
        flexWrap: 'wrap',
      }}>
        {FILTER_TABS.map((tab) => {
          const active = filter === tab;
          const tabColor = tab === 'HIGH' ? '#ef4444' : tab === 'MEDIUM' ? '#f59e0b' : tab === 'LOW' ? '#22c55e' : '#4f72ff';
          return (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              style={{
                padding: '5px 14px',
                borderRadius: 99,
                border: `1px solid ${active ? tabColor : 'rgba(255,255,255,0.08)'}`,
                background: active ? `${tabColor}18` : 'transparent',
                color: active ? tabColor : '#64748b',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: 'Inter, sans-serif',
                transition: 'all 0.15s ease',
              }}
            >
              {tab}
              {tab !== 'ALL' && (
                <span style={{ marginLeft: 5, opacity: 0.7 }}>
                  {counts[tab] || 0}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Scrollable clause list ── */}
      <div style={{
        maxHeight: 620,
        overflowY: 'auto',
        paddingRight: 4,
      }}>
        {filtered.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px 0',
            color: '#475569',
            fontSize: 14,
          }}>
            No {filter.toLowerCase()} risk clauses found.
          </div>
        ) : (
          filtered.map((result, idx) => (
            <ClauseCard key={idx} result={result} index={idx} />
          ))
        )}
      </div>
    </div>
  );
}

export default ResultsList;
