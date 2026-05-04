import React, { useEffect, useMemo, useState } from 'react';
import ChatPanel from './ChatPanel';
import { exportAnalysisReportPdf } from '../utils/exportAnalysisPdf';
import { cleanClauseDisplayText, cleanDisplayText } from '../utils/textSanitizer';

function getRiskToken(level) {
  switch (level) {
    case 'HIGH':   return { bg: 'var(--risk-high-bg)', color: 'var(--risk-high)', border: 'var(--risk-high-border)', label: 'Careful' };
    case 'MEDIUM': return { bg: 'var(--risk-med-bg)', color: 'var(--risk-med)', border: 'var(--risk-med-border)', label: 'Review' };
    case 'LOW':    return { bg: 'var(--risk-low-bg)', color: 'var(--risk-low)', border: 'var(--risk-low-border)', label: 'Standard' };
    default:       return { bg: '#f3f4f6', color: '#4b5563', border: '#d1d5db', label: 'Unknown' };
  }
}

export default function AnalysisView({
  results = [],
  chatSessionId,
  chatMessages,
  onChatSend,
  chatLoading,
  agreementType,
  userType,
}) {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const [mobilePane, setMobilePane] = useState('explanation');
  const [summaryCollapsed, setSummaryCollapsed] = useState(true);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [showFullExplanation, setShowFullExplanation] = useState(false);

  if (!results || results.length === 0) return null;

  const activeIdx = Math.min(selectedIdx, Math.max(0, results.length - 1));
  const selected = results[activeIdx];
  const risk = getRiskToken(selected?.risk_level);

  const highCount = useMemo(() => results.filter((r) => r.risk_level === 'HIGH').length, [results]);
  const mediumCount = useMemo(() => results.filter((r) => r.risk_level === 'MEDIUM').length, [results]);
  const lowCount = useMemo(() => results.filter((r) => r.risk_level === 'LOW').length, [results]);
  const highClauseRefs = useMemo(
    () => results.map((r, idx) => (r.risk_level === 'HIGH' ? `C${idx + 1}` : null)).filter(Boolean),
    [results]
  );
  const mediumClauseRefs = useMemo(
    () => results.map((r, idx) => (r.risk_level === 'MEDIUM' ? `C${idx + 1}` : null)).filter(Boolean),
    [results]
  );
  const lowClauseRefs = useMemo(
    () => results.map((r, idx) => (r.risk_level === 'LOW' ? `C${idx + 1}` : null)).filter(Boolean),
    [results]
  );
  const totalCount = results.length;

  const weightedRiskScore = Math.round(
    ((highCount * 100) + (mediumCount * 60) + (lowCount * 20)) / Math.max(1, totalCount)
  );

  const scoreLabel = weightedRiskScore >= 70
    ? 'High Contract Exposure'
    : weightedRiskScore >= 40
      ? 'Moderate Contract Exposure'
      : 'Low Contract Exposure';

  const scoreTone = weightedRiskScore >= 70
    ? { bg: 'var(--risk-high-bg)', color: 'var(--risk-high)', border: 'var(--risk-high-border)' }
    : weightedRiskScore >= 40
      ? { bg: 'var(--risk-med-bg)', color: 'var(--risk-med)', border: 'var(--risk-med-border)' }
      : { bg: 'var(--risk-low-bg)', color: 'var(--risk-low)', border: 'var(--risk-low-border)' };

  const explanationText = cleanDisplayText(
    selected?.explanation || 'This clause operates on standardized terms with low legal exposure.'
  );
  const hasLongExplanation = explanationText.length > 280;
  const explanationPreview = hasLongExplanation && !showFullExplanation
    ? `${explanationText.slice(0, 280).trim()}...`
    : explanationText;

  const formatClauseRefs = (refs) => {
    if (!refs || refs.length === 0) {
      return 'None';
    }
    if (refs.length <= 8) {
      return refs.join(', ');
    }
    return `${refs.slice(0, 8).join(', ')}, +${refs.length - 8} more`;
  };

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 1180);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (selectedIdx > results.length - 1) {
      setSelectedIdx(Math.max(0, results.length - 1));
    }
  }, [results, selectedIdx]);

  useEffect(() => {
    setShowFullExplanation(false);
  }, [activeIdx]);

  const handleExportPdf = async () => {
    if (exportingPdf) {
      return;
    }

    setExportingPdf(true);
    try {
      exportAnalysisReportPdf({
        results,
        agreementType,
        userType,
        generatedAt: new Date(),
      });
    } catch (err) {
      console.error(err);
      alert(err?.message || 'Unable to export PDF report.');
    } finally {
      setExportingPdf(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0' }}>
      
      {/* Top Banner Context */}
      <div style={{ padding: '24px 32px', background: '#fff', borderBottom: '1px solid var(--border-light)' }}>
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-title)' }}>Contract Analysis</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{results.length} clauses parsed &middot; {highCount} careful-review clauses found</p>
              <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, fontWeight: 600, background: '#f3f4f6', color: '#111827', borderRadius: 999, padding: '4px 10px' }}>
                  {cleanDisplayText(agreementType || 'Agreement not set')}
                </span>
                <span style={{ fontSize: 12, fontWeight: 600, background: '#eef2ff', color: '#312e81', borderRadius: 999, padding: '4px 10px' }}>
                  Perspective: {cleanDisplayText(userType || 'Role not set')}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button
                className="btn-outline"
                onClick={() => setSummaryCollapsed((prev) => !prev)}
                style={{ padding: '8px 12px', fontSize: 12 }}
              >
                {summaryCollapsed ? 'Expand Exposure' : 'Collapse Exposure'}
              </button>
              <button
                className="btn-primary"
                onClick={handleExportPdf}
                disabled={exportingPdf}
                style={{ padding: '8px 12px', fontSize: 12 }}
              >
                {exportingPdf ? 'Exporting...' : 'Export PDF'}
              </button>
            </div>
         </div>

         <div style={{ marginTop: 12, padding: summaryCollapsed ? '10px 12px' : '14px 16px', border: '1px solid var(--border-light)', borderRadius: 10, background: '#fafafa' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-title)', margin: 0 }}>Exposure Summary</h3>
                {!summaryCollapsed && (
                  <p style={{ margin: '5px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>
                    Quick contract risk snapshot with interpretable clause categories.
                  </p>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '6px 10px', borderRadius: 8,
                  background: scoreTone.bg, border: `1px solid ${scoreTone.border}`
                }}>
                  <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase', color: scoreTone.color }}>
                    Risk Score
                  </span>
                  <span style={{ fontSize: 18, fontWeight: 800, color: scoreTone.color, lineHeight: 1 }}>
                    {weightedRiskScore}
                  </span>
                </div>
              </div>
            </div>

            {summaryCollapsed && (
              <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 999, border: '1px solid var(--risk-high-border)', background: 'var(--risk-high-bg)', color: 'var(--risk-high)' }}>
                  High {highCount}
                </span>
                <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 999, border: '1px solid var(--risk-med-border)', background: 'var(--risk-med-bg)', color: 'var(--risk-med)' }}>
                  Medium {mediumCount}
                </span>
                <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 999, border: '1px solid var(--risk-low-border)', background: 'var(--risk-low-bg)', color: 'var(--risk-low)' }}>
                  Low {lowCount}
                </span>
                <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 999, border: '1px solid var(--border-light)', background: '#ffffff', color: 'var(--text-body)' }}>
                  {scoreLabel}
                </span>
              </div>
            )}

            {!summaryCollapsed && (
            <>
            <div style={{ marginTop: 12, marginBottom: 10 }}>
              <div style={{ height: 6, borderRadius: 999, overflow: 'hidden', background: '#e5e7eb', display: 'flex' }}>
                <div style={{ width: `${(highCount / Math.max(1, totalCount)) * 100}%`, background: 'var(--risk-high)' }} />
                <div style={{ width: `${(mediumCount / Math.max(1, totalCount)) * 100}%`, background: 'var(--risk-med)' }} />
                <div style={{ width: `${(lowCount / Math.max(1, totalCount)) * 100}%`, background: 'var(--risk-low)' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8 }}>
              <div style={{ border: '1px solid var(--risk-high-border)', background: 'var(--risk-high-bg)', borderRadius: 8, padding: 9 }}>
                <p style={{ margin: 0, fontSize: 11, fontWeight: 700, color: 'var(--risk-high)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>High-Risk Clauses</p>
                <p style={{ margin: '4px 0 0', fontSize: 17, fontWeight: 800, color: 'var(--risk-high)' }}>{highCount}</p>
                <p style={{ margin: '5px 0 0', fontSize: 11, color: 'var(--risk-high)', lineHeight: 1.4 }}>
                  {formatClauseRefs(highClauseRefs)}
                </p>
              </div>
              <div style={{ border: '1px solid var(--risk-med-border)', background: 'var(--risk-med-bg)', borderRadius: 8, padding: 9 }}>
                <p style={{ margin: 0, fontSize: 11, fontWeight: 700, color: 'var(--risk-med)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Moderate Risks</p>
                <p style={{ margin: '4px 0 0', fontSize: 17, fontWeight: 800, color: 'var(--risk-med)' }}>{mediumCount}</p>
                <p style={{ margin: '5px 0 0', fontSize: 11, color: 'var(--risk-med)', lineHeight: 1.4 }}>
                  {formatClauseRefs(mediumClauseRefs)}
                </p>
              </div>
              <div style={{ border: '1px solid var(--risk-low-border)', background: 'var(--risk-low-bg)', borderRadius: 8, padding: 9 }}>
                <p style={{ margin: 0, fontSize: 11, fontWeight: 700, color: 'var(--risk-low)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Safe Sections</p>
                <p style={{ margin: '4px 0 0', fontSize: 17, fontWeight: 800, color: 'var(--risk-low)' }}>{lowCount}</p>
                <p style={{ margin: '5px 0 0', fontSize: 11, color: 'var(--risk-low)', lineHeight: 1.4 }}>
                  {formatClauseRefs(lowClauseRefs)}
                </p>
              </div>
            </div>

            <p style={{ margin: '10px 0 0', fontSize: 12, color: 'var(--text-body)' }}>
              {scoreLabel}. This dashboard summarizes clause-level complexity into decision-ready indicators.
            </p>
            </>
            )}
         </div>
      </div>

      {!isMobile ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(300px, 34%) minmax(360px, 36%) minmax(340px, 30%)',
            flex: 1,
            minHeight: 0,
          }}
        >
          <section style={{ borderRight: '1px solid var(--border-light)', background: 'var(--bg-main)', minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '14px 18px', fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Clause Navigator
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {results.map((r, i) => {
                const st = getRiskToken(r.risk_level);
                const isSel = activeIdx === i;
                return (
                  <button
                    key={i}
                    onClick={() => setSelectedIdx(i)}
                    style={{
                      textAlign: 'left',
                      padding: 14,
                      background: isSel ? '#ffffff' : '#f8fafc',
                      border: `1px solid ${isSel ? 'var(--border-strong)' : 'var(--border-light)'}`,
                      borderRadius: 10,
                      cursor: 'pointer',
                      borderLeft: `4px solid ${st.color}`,
                      boxShadow: isSel ? '0 4px 14px rgba(15, 23, 42, 0.08)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-title)' }}>Clause {i + 1}</span>
                      <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 999, background: st.bg, color: st.color }}>
                        {st.label}
                      </span>
                    </div>
                    <p
                      style={{
                        margin: 0,
                        fontSize: 13,
                        color: 'var(--text-body)',
                        lineHeight: 1.45,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {cleanClauseDisplayText(r.clause)}
                    </p>
                  </button>
                );
              })}
            </div>
          </section>

          <section style={{ borderRight: '1px solid var(--border-light)', background: '#ffffff', minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-title)' }}>Risk Explanation</h3>
                <span style={{ fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 999, background: risk.bg, color: risk.color, border: `1px solid ${risk.border}` }}>
                  {risk.label} Exposure
                </span>
              </div>
            </div>

            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: 20 }}>
              <div style={{ marginBottom: 18, padding: 14, border: '1px solid var(--border-light)', borderRadius: 10, background: '#f8fafc' }}>
                <h4 style={{ margin: '0 0 8px', fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Selected Clause
                </h4>
                <p style={{ margin: 0, fontSize: 14, color: 'var(--text-body)', lineHeight: 1.65 }}>
                  {cleanClauseDisplayText(selected?.clause)}
                </p>
              </div>

              <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 700, color: 'var(--text-title)' }}>What this means</h4>
              <p style={{ margin: 0, fontSize: 14, color: 'var(--text-body)', lineHeight: 1.6 }}>
                {explanationPreview}
              </p>

              {hasLongExplanation && (
                <button
                  className="btn-outline"
                  onClick={() => setShowFullExplanation((prev) => !prev)}
                  style={{ marginTop: 10, padding: '6px 10px', fontSize: 12 }}
                >
                  {showFullExplanation ? 'Show Less' : 'Show More'}
                </button>
              )}

              {selected?.similar_clauses?.length > 0 && (
                <div style={{ marginTop: 20 }}>
                  <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 700, color: 'var(--text-title)' }}>Reference Matches</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {selected.similar_clauses.slice(0, 3).map((sc, i) => (
                      <div key={i} style={{ padding: 12, background: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 8 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 4 }}>
                          {cleanDisplayText(sc.document || sc.clause_type || 'Knowledge Base')}
                        </div>
                        <p style={{ margin: 0, fontSize: 13, color: 'var(--text-body)', lineHeight: 1.45 }}>
                          "{cleanClauseDisplayText(sc.text)}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>

          <section style={{ background: '#f8fafc', minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-light)', background: '#ffffff' }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-title)' }}>AI Assistant</h3>
              <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>
                Asking about Clause {activeIdx + 1} with {risk.label.toLowerCase()} context.
              </p>
            </div>
            <div style={{ flex: 1, minHeight: 0, padding: 16 }}>
              <ChatPanel
                sessionId={chatSessionId}
                messages={chatMessages}
                loading={chatLoading}
                onSend={(question) => onChatSend(question, activeIdx)}
              />
            </div>
          </section>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
          <section style={{ borderBottom: '1px solid var(--border-light)', background: 'var(--bg-main)', maxHeight: 260, minHeight: 220, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '12px 16px', fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Clause Navigator
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {results.map((r, i) => {
                const st = getRiskToken(r.risk_level);
                const isSel = activeIdx === i;
                return (
                  <button
                    key={i}
                    onClick={() => setSelectedIdx(i)}
                    style={{
                      textAlign: 'left',
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: `1px solid ${isSel ? 'var(--border-strong)' : 'var(--border-light)'}`,
                      background: isSel ? '#ffffff' : '#f8fafc',
                      borderLeft: `4px solid ${st.color}`,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-title)' }}>Clause {i + 1}</span>
                      <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 999, background: st.bg, color: st.color }}>
                        {st.label}
                      </span>
                    </div>
                    <p
                      style={{
                        margin: 0,
                        fontSize: 12,
                        color: 'var(--text-body)',
                        lineHeight: 1.4,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {cleanClauseDisplayText(r.clause)}
                    </p>
                  </button>
                );
              })}
            </div>
          </section>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', padding: 10, gap: 8, borderBottom: '1px solid var(--border-light)', background: '#ffffff' }}>
            <button
              className={mobilePane === 'explanation' ? 'btn-primary' : 'btn-outline'}
              onClick={() => setMobilePane('explanation')}
              style={{ padding: '8px 10px', fontSize: 12 }}
            >
              Explanation
            </button>
            <button
              className={mobilePane === 'chat' ? 'btn-primary' : 'btn-outline'}
              onClick={() => setMobilePane('chat')}
              style={{ padding: '8px 10px', fontSize: 12 }}
            >
              Chat
            </button>
          </div>

          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden', background: '#ffffff' }}>
            {mobilePane === 'explanation' ? (
              <div style={{ height: '100%', overflowY: 'auto', padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-title)' }}>Risk Explanation</h3>
                  <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 999, background: risk.bg, color: risk.color, border: `1px solid ${risk.border}` }}>
                    {risk.label}
                  </span>
                </div>

                <div style={{ marginBottom: 14, padding: 12, borderRadius: 10, border: '1px solid var(--border-light)', background: '#f8fafc' }}>
                  <h4 style={{ margin: '0 0 8px', fontSize: 12, color: 'var(--text-muted)' }}>Clause {activeIdx + 1}</h4>
                  <p style={{ margin: 0, fontSize: 13, color: 'var(--text-body)', lineHeight: 1.55 }}>{cleanClauseDisplayText(selected?.clause)}</p>
                </div>

                <p style={{ margin: 0, fontSize: 14, color: 'var(--text-body)', lineHeight: 1.6 }}>{explanationPreview}</p>
                {hasLongExplanation && (
                  <button
                    className="btn-outline"
                    onClick={() => setShowFullExplanation((prev) => !prev)}
                    style={{ marginTop: 10, padding: '6px 10px', fontSize: 12 }}
                  >
                    {showFullExplanation ? 'Show Less' : 'Show More'}
                  </button>
                )}
              </div>
            ) : (
              <div style={{ height: '100%', padding: 12 }}>
                <ChatPanel
                  sessionId={chatSessionId}
                  messages={chatMessages}
                  loading={chatLoading}
                  onSend={(question) => onChatSend(question, activeIdx)}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
