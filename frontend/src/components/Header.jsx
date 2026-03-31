import React from 'react';

function Header() {
  return (
    <header style={{ textAlign: 'center', padding: '48px 0 32px' }}>
      {/* Geometric Logo */}
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 72,
        height: 72,
        borderRadius: 20,
        background: 'linear-gradient(135deg, rgba(107,67,255,0.1), rgba(139,92,246,0.25))',
        border: '1px solid rgba(139,92,246,0.3)',
        marginBottom: 24,
        boxShadow: '0 8px 32px rgba(139,92,246,0.25), inset 0 2px 0 rgba(255,255,255,0.1)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Glow effect inside */}
        <div style={{
          position: 'absolute',
          top: -20, right: -20, width: 40, height: 40,
          background: '#8b5cf6', filter: 'blur(30px)', opacity: 0.5
        }} />
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
          {/* A futuristic abstract nexus / document shape */}
          <path d="M12 2L22 7L12 12L2 7L12 2Z" stroke="url(#logo-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="url(#logo-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="url(#logo-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <circle cx="12" cy="12" r="3" fill="#a78bfa" />
          <defs>
            <linearGradient id="logo-grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
              <stop stopColor="#f3f0ff" />
              <stop offset="0.5" stopColor="#a78bfa" />
              <stop offset="1" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <h1 style={{
        fontSize: 'clamp(26px, 4vw, 38px)',
        fontWeight: 800,
        letterSpacing: '-0.02em',
        background: 'linear-gradient(135deg, #f3f0ff 30%, #b1a4f0)',
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
          background: 'linear-gradient(90deg, #8b5cf6, #a78bfa)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          AI Contract Risk Analyzer
        </span>
      </h1>

      <p style={{
        color: '#7b6aae',
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
        background: 'linear-gradient(90deg, transparent, #8b5cf6, transparent)',
        margin: '24px auto 0',
        borderRadius: 99,
      }} />
    </header>
  );
}

export default Header;
