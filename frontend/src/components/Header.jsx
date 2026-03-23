import React from 'react';

function Header() {
  return (
    <header style={{ textAlign: 'center', padding: '48px 0 32px' }}>
      {/* Shield logo */}
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 64,
        height: 64,
        borderRadius: 16,
        background: 'linear-gradient(135deg, #3b5bdb22, #4f72ff33)',
        border: '1px solid #4f72ff44',
        marginBottom: 20,
        boxShadow: '0 0 32px rgba(79,114,255,0.18)',
      }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2L3 6v6c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V6L12 2z"
            fill="url(#shield-grad)"
          />
          <path d="M9 12l2 2 4-4" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <defs>
            <linearGradient id="shield-grad" x1="3" y1="2" x2="21" y2="23" gradientUnits="userSpaceOnUse">
              <stop stopColor="#3b5bdb" />
              <stop offset="1" stopColor="#4f72ff" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <h1 style={{
        fontSize: 'clamp(26px, 4vw, 38px)',
        fontWeight: 800,
        letterSpacing: '-0.02em',
        background: 'linear-gradient(135deg, #e8ecf4 30%, #94a3b8)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        marginBottom: 10,
      }}>
        LexGuard
        <span style={{
          marginLeft: 10,
          fontSize: 'clamp(14px, 2vw, 18px)',
          fontWeight: 500,
          background: 'linear-gradient(90deg, #4f72ff, #7c9dff)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          AI Contract Risk Analyzer
        </span>
      </h1>

      <p style={{
        color: '#64748b',
        fontSize: '15px',
        fontWeight: 400,
        maxWidth: 480,
        margin: '0 auto',
        lineHeight: 1.6,
      }}>
        Upload any contract PDF. Our AI extracts clauses, queries 9,000+ legal precedents,
        and classifies risk in seconds.
      </p>

      {/* Decorative divider */}
      <div style={{
        width: 60,
        height: 2,
        background: 'linear-gradient(90deg, transparent, #4f72ff, transparent)',
        margin: '24px auto 0',
        borderRadius: 99,
      }} />
    </header>
  );
}

export default Header;
