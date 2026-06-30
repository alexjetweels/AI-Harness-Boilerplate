import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Play, Zap, Upload, FileText, FileSpreadsheet, X, Paperclip } from 'lucide-react';
import { API_BASE, DEFAULT_TASK, AppNav } from '../shared';

/* ── File type helpers ─────────────────────────────────────────────────────── */

const ACCEPTED_TYPES = {
  'application/pdf':                                            { label: 'PDF',   className: 'chip-pdf'   },
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': { label: 'XLSX', className: 'chip-excel' },
  'application/vnd.ms-excel':                                  { label: 'XLS',   className: 'chip-excel' },
  'text/plain':                                                 { label: 'TXT',   className: 'chip-txt'   },
};
const ACCEPTED_EXT = '.pdf,.xlsx,.xls,.txt';

function fileTypeMeta(file) {
  return (
    ACCEPTED_TYPES[file.type] ||
    (file.name.endsWith('.xlsx') ? { label: 'XLSX', className: 'chip-excel' } :
     file.name.endsWith('.xls')  ? { label: 'XLS',  className: 'chip-excel' } :
     file.name.endsWith('.pdf')  ? { label: 'PDF',  className: 'chip-pdf'   } :
                                   { label: 'TXT',  className: 'chip-txt'   })
  );
}

function fmtSize(bytes) {
  if (bytes < 1024)       return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function FileIcon({ file }) {
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (ext === 'xlsx' || ext === 'xls') return <FileSpreadsheet size={13} aria-hidden />;
  return <FileText size={13} aria-hidden />;
}

/* ── FileUploadZone ─────────────────────────────────────────────────────────── */

function FileUploadZone({ files, onChange }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const addFiles = useCallback((incoming) => {
    const valid = Array.from(incoming).filter((f) => ACCEPTED_TYPES[f.type] ||
      /\.(pdf|xlsx?|txt)$/i.test(f.name));
    if (!valid.length) return;
    onChange((prev) => {
      const seen = new Set(prev.map((f) => f.name + f.size));
      return [...prev, ...valid.filter((f) => !seen.has(f.name + f.size))];
    });
  }, [onChange]);

  const removeFile = (index) =>
    onChange((prev) => prev.filter((_, i) => i !== index));

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  };

  return (
    <div className="uploadSection">
      <label htmlFor="file-upload-input">
        <span>Attachments <small className="uploadLabel-hint">PDF · XLSX · XLS · TXT</small></span>
      </label>

      {/* drop zone */}
      <div
        className={`uploadZone${dragging ? ' uploadZone--active' : ''}`}
        role="button"
        tabIndex={0}
        aria-label="Upload files — click or drop here"
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
        onDragEnter={(e) => { e.preventDefault(); setDragging(true); }}
        onDragOver={(e)  => { e.preventDefault(); setDragging(true); }}
        onDragLeave={(e) => { e.preventDefault(); setDragging(false); }}
        onDrop={onDrop}
      >
        <Upload size={16} className="uploadZone-icon" aria-hidden />
        <span className="uploadZone-text">
          {dragging ? 'Drop to attach' : 'Click or drag files here'}
        </span>
      </div>

      <input
        id="file-upload-input"
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXT}
        multiple
        className="uploadInput-hidden"
        aria-label="Select files"
        onChange={(e) => { addFiles(e.target.files); e.target.value = ''; }}
      />

      {/* file chips */}
      {files.length > 0 && (
        <ul className="fileChipList" aria-label="Attached files">
          {files.map((file, i) => {
            const meta = fileTypeMeta(file);
            return (
              <li key={`${file.name}-${file.size}`} className="fileChip">
                <FileIcon file={file} />
                <span className={`fileChip-type ${meta.className}`}>{meta.label}</span>
                <span className="fileChip-name" title={file.name}>{file.name}</span>
                <span className="fileChip-size">{fmtSize(file.size)}</span>
                <button
                  type="button"
                  className="fileChip-remove"
                  aria-label={`Remove ${file.name}`}
                  onClick={() => removeFile(i)}
                >
                  <X size={11} aria-hidden />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/* ── Upload files after run created ────────────────────────────────────────── */

async function uploadFiles(files, runId) {
  if (!files.length) return;
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  try {
    await fetch(`${API_BASE}/api/file-extractions?run_id=${encodeURIComponent(runId)}`, {
      method: 'POST',
      body: form,
    });
  } catch {
    // Silently swallow — extraction endpoint may not be wired yet.
  }
}

/* ── LaunchForm ─────────────────────────────────────────────────────────────── */

function LaunchForm({ onRunStarted }) {
  const [feature,  setFeature]  = useState(DEFAULT_TASK);
  const [provider, setProvider] = useState('claude');
  const [mode,     setMode]     = useState('expanded');
  const [files,    setFiles]    = useState([]);
  const [starting, setStarting] = useState(false);
  const [error,    setError]    = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setStarting(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/harness-runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feature, provider, mode }),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const payload = await res.json();
      // Upload files in background — don't block navigation.
      uploadFiles(files, payload.id);
      onRunStarted(payload.id);
    } catch (err) {
      setError(err.message || 'Failed to start run');
    } finally {
      setStarting(false);
    }
  }

  return (
    <section className="launchCard">
      <h2 className="launchCard-title">
        <Zap size={15} />
        New Run
      </h2>
      {error && <div className="errorLine">{error}</div>}
      <form onSubmit={handleSubmit} className="launchCard-form">
        <label>
          <span>Task / Feature</span>
          <textarea value={feature} onChange={(e) => setFeature(e.target.value)} rows={3} />
        </label>

        <FileUploadZone files={files} onChange={setFiles} />

        <div className="launchCard-row2">
          <label>
            <span>Provider</span>
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="codex">Codex</option>
              <option value="claude">Claude Code</option>
            </select>
          </label>
          <label>
            <span>Mode</span>
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="expanded">Expanded</option>
              <option value="boss">Boss</option>
            </select>
          </label>
          <button className="primaryButton" type="submit" disabled={starting || !feature.trim()}>
            {starting ? <Activity className="spin" size={14} /> : <Play size={14} />}
            {files.length > 0
              ? `Start Run · ${files.length} file${files.length > 1 ? 's' : ''}`
              : 'Start Run'}
          </button>
        </div>
      </form>
    </section>
  );
}

export default function ExecutePage() {
  const navigate = useNavigate();

  return (
    <div className="dashPage">
      <AppNav />
      <div className="dashContent">
        <LaunchForm onRunStarted={(runId) => navigate(`/pipeline/${runId}`)} />
      </div>
    </div>
  );
}
