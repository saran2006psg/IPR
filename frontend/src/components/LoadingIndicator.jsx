import React, { useEffect, useState } from 'react';

const STAGES = [
  { id: 1, label: 'Extracting PDF text',       icon: '📄' },
  { id: 2, label: 'Segmenting clauses',         icon: '✂️' },
  { id: 3, label: 'Generating embeddings',      icon: '🧮' },
  { id: 4, label: 'Querying knowledge base',    icon: '🔍' },
  { id: 5, label: 'Analyzing risk with RoBERTa',icon: '🤖' },
];

function LoadingIndicator() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActive((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 3800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '40px 16px',
      gap: 32,
    }}>
      {/* Spinner */}
      <div style={{ position: 'relative', width: 72, height: 72 }}>
        <div style={{
          position: 'absolute', inset: 0,
          borderRadius: '50%',
          border: '3px solid rgba(139,92,246,0.15)',
        }} />
        <div style={{
          position: 'absolute', inset: 0,
          borderRadius: '50%',
          border: '3px solid transparent',
          borderTopColor: '#8b5cf6',
          animation: 'spin 0.9s linear infinite',
        }} />
        <div style={{
          position: 'absolute',
          inset: '14px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #6b43ff22, #8b5cf633)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22,
        }}>
          {STAGES[active].icon}
        </div>
      </div>

      {/* Stage label */}
      <div style={{ textAlign: 'center' }}>
        <p style={{ color: '#f3f0ff', fontWeight: 600, fontSize: 16, marginBottom: 4 }}>
          {STAGES[active].label}…
        </p>
        <p style={{ color: '#7b6aae', fontSize: 13 }}>
          Step {active + 1} of {STAGES.length}
        </p>
      </div>

      {/* Steps list */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        width: '100%',
        maxWidth: 380,
      }}>
        {STAGES.map((stage, idx) => {
          const done    = idx < active;
          const current = idx === active;
          return (
            <div key={stage.id} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 14px',
              borderRadius: 8,
              background: current
                ? 'rgba(139,92,246,0.1)'
                : done ? 'rgba(16,185,129,0.07)' : 'rgba(255,255,255,0.02)',
              border: `1px solid ${current ? 'rgba(139,92,246,0.3)' : done ? 'rgba(16,185,129,0.2)' : 'rgba(255,255,255,0.04)'}`,
              transition: 'all 0.3s ease',
            }}>
              {/* Step indicator */}
              <div style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 11,
                fontWeight: 700,
                background: done ? '#10b981' : current ? '#8b5cf6' : 'rgba(255,255,255,0.06)',
                color: done || current ? '#fff' : '#5a4a9c',
              }}>
                {done ? (
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                    <path d="M20 6L9 17l-5-5" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : stage.id}
              </div>
              <span style={{
                fontSize: 13,
                fontWeight: current ? 600 : 400,
                color: done ? '#10b981' : current ? '#f3f0ff' : '#5a4a9c',
                flex: 1,
              }}>
                {stage.label}
              </span>
              {current && (
                <div style={{
                  width: 6, height: 6,
                  borderRadius: '50%',
                  background: '#8b5cf6',
                  animation: 'spin 1s ease-in-out infinite',
                  boxShadow: '0 0 6px #8b5cf6',
                }} />
              )}
            </div>
          );
        })}
      </div>

      <p style={{ color: '#334155', fontSize: 12 }}>
        Please keep this tab open while analysis runs
      </p>
    </div>
  );
}

export default LoadingIndicator;
