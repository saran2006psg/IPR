import React, { useState } from 'react';
import ChatPanel from './ChatPanel';

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

  if (!results || results.length === 0) return null;

  const selected = results[selectedIdx];
  const risk = getRiskToken(selected?.risk_level);
  const highCount = results.filter(r => r.risk_level === 'HIGH').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0' }}>
      
      {/* Top Banner Context */}
      <div style={{ padding: '24px 32px', background: '#fff', borderBottom: '1px solid var(--border-light)' }}>
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-title)' }}>Contract Analysis</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{results.length} clauses parsed &middot; {highCount} careful-review clauses found</p>
              <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, fontWeight: 600, background: '#f3f4f6', color: '#111827', borderRadius: 999, padding: '4px 10px' }}>
                  {agreementType || 'Agreement not set'}
                </span>
                <span style={{ fontSize: 12, fontWeight: 600, background: '#eef2ff', color: '#312e81', borderRadius: 999, padding: '4px 10px' }}>
                  Perspective: {userType || 'Role not set'}
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button className="btn-outline">Export PDF</button>
              <button className="btn-primary">Resolve Tasks</button>
            </div>
         </div>
      </div>

      {/* Main Split Interface */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
        
        {/* Left pane: Clauses List */}
        <div style={{ flex: '1', borderRight: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', background: 'var(--bg-main)' }}>
          <div style={{ padding: '16px 24px', fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Document Flow
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
             {results.map((r, i) => {
               const st = getRiskToken(r.risk_level);
               const isSel = selectedIdx === i;
               return (
                 <div
                   key={i}
                   onClick={() => setSelectedIdx(i)}
                   style={{
                     padding: 16, background: isSel ? '#fff' : 'transparent',
                     border: `1px solid ${isSel ? 'var(--border-strong)' : 'transparent'}`,
                     borderRadius: 8, cursor: 'pointer',
                     boxShadow: isSel ? '0 1px 3px rgba(0,0,0,0.05)' : 'none',
                     borderLeft: `4px solid ${isSel ? st.color : 'transparent'}`,
                     transition: 'all 0.1s'
                   }}
                 >
                   <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, alignItems: 'center' }}>
                     <span style={{ fontSize: 13, fontWeight: 600, color: isSel ? 'var(--text-title)' : 'var(--text-muted)' }}>Clause {i + 1}</span>
                     {r.risk_level !== 'LOW' && (
                       <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 12, background: st.bg, color: st.color }}>
                         {st.label}
                       </span>
                     )}
                   </div>
                   <div style={{ 
                     fontSize: 14, color: 'var(--text-body)', lineHeight: 1.6,
                     display: '-webkit-box', WebkitLineClamp: isSel ? 'none' : '2', WebkitBoxOrient: 'vertical', overflow: 'hidden'
                   }}>
                     {r.clause}
                   </div>
                 </div>
               );
             })}
          </div>
        </div>

        {/* Right pane: Insight & Chat */}
        <div style={{ width: 480, display: 'flex', flexDirection: 'column', background: '#fff' }}>
          
          {/* Selected Insights Top */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 24, borderBottom: '1px solid var(--border-light)' }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
               <span style={{ fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 4, background: risk.bg, color: risk.color, border: `1px solid ${risk.border}` }}>
                 {risk.label} Exposure
               </span>
             </div>
             
             <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-title)', marginBottom: 8 }}>Risk Explanation</h3>
             <p style={{ fontSize: 14, color: 'var(--text-body)', lineHeight: 1.5, marginBottom: 24 }}>
               {selected?.explanation || 'This clause operates on standardized terms with low legal exposure.'}
             </p>

             {selected?.similar_clauses?.length > 0 && (
               <div>
                 <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-title)', marginBottom: 8 }}>Precedence Matches</h3>
                 <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                   {selected.similar_clauses.slice(0, 2).map((sc, i) => (
                     <div key={i} style={{ padding: 12, background: 'var(--bg-main)', border: `1px solid var(--border-light)`, borderRadius: 6 }}>
                       <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>Match from: {sc.document || sc.clause_type}</div>
                       <div style={{ fontSize: 13, color: 'var(--text-body)', lineHeight: 1.4 }}>"{sc.text}"</div>
                     </div>
                   ))}
                 </div>
               </div>
             )}
          </div>

          {/* Chat Panel Bottom */}
          <div style={{ height: 400, display: 'flex', flexDirection: 'column', padding: 24, background: '#f9fafb' }}>
             <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-title)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                AI Assistant
             </h3>
             <div style={{ flex: 1, minHeight: 0 }}>
               <ChatPanel 
                 sessionId={chatSessionId}
                 messages={chatMessages}
                 loading={chatLoading}
                 onSend={(question) => onChatSend(question, selectedIdx)}
               />
             </div>
          </div>

        </div>

      </div>
    </div>
  );
}
