import React, { useCallback, useState } from 'react';

function FileUpload({ onFileSelect, selectedFile, onAnalyze, disabled }) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.toLowerCase().endsWith('.pdf')) {
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileSelect(file);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div style={{ padding: '8px 0 24px' }}>
      {/* Drop zone */}
      <label
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          padding: '48px 24px',
          borderRadius: 14,
          border: `2px dashed ${dragging ? '#4f72ff' : selectedFile ? '#22c55e55' : '#2d3a52'}`,
          background: dragging
            ? 'rgba(79,114,255,0.07)'
            : selectedFile
              ? 'rgba(34,197,94,0.05)'
              : 'rgba(17,24,39,0.5)',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: dragging ? '0 0 24px rgba(79,114,255,0.15)' : 'none',
        }}
      >
        <input
          type="file"
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={handleInputChange}
          disabled={disabled}
        />

        {/* Upload icon */}
        {!selectedFile ? (
          <>
            <div style={{
              width: 56,
              height: 56,
              borderRadius: 12,
              background: 'rgba(79,114,255,0.12)',
              border: '1px solid rgba(79,114,255,0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="#4f72ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <polyline points="17,8 12,3 7,8" stroke="#4f72ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <line x1="12" y1="3" x2="12" y2="15" stroke="#4f72ff" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ color: '#e8ecf4', fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
                Drop your contract PDF here
              </p>
              <p style={{ color: '#64748b', fontSize: 13 }}>
                or <span style={{ color: '#4f72ff', fontWeight: 600 }}>click to browse</span> — PDF only
              </p>
            </div>
          </>
        ) : (
          /* File selected chip */
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '14px 20px',
            background: 'rgba(34,197,94,0.08)',
            border: '1px solid rgba(34,197,94,0.25)',
            borderRadius: 10,
            width: '100%',
            maxWidth: 440,
          }}>
            {/* PDF icon */}
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 8,
              background: 'rgba(239,68,68,0.15)',
              border: '1px solid rgba(239,68,68,0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"
                  stroke="#ef4444" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                <polyline points="14,2 14,8 20,8" stroke="#ef4444" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <p style={{ color: '#e8ecf4', fontWeight: 600, fontSize: 14,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedFile.name}
              </p>
              <p style={{ color: '#64748b', fontSize: 12, marginTop: 2 }}>
                {formatSize(selectedFile.size)}
              </p>
            </div>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="#22c55e" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        )}
      </label>

      {/* Hint */}
      {!selectedFile && (
        <p style={{ textAlign: 'center', color: '#475569', fontSize: 12, marginTop: 10 }}>
          Supported: employment, NDA, SaaS, lease, and other legal contracts
        </p>
      )}

      {/* Analyze button */}
      {selectedFile && (
        <div style={{ textAlign: 'center', marginTop: 28 }}>
          <button
            className="btn-primary"
            onClick={onAnalyze}
            disabled={disabled}
            style={{ fontSize: 16, padding: '14px 40px', minWidth: 220 }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="8" stroke="white" strokeWidth="2"/>
              <path d="m21 21-4.35-4.35" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Analyze Contract
          </button>
          <p style={{ color: '#475569', fontSize: 12, marginTop: 10 }}>
            Takes 15–60 s depending on contract length
          </p>
        </div>
      )}
    </div>
  );
}

export default FileUpload;
