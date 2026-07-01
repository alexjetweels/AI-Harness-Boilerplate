import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Play, Zap, Upload, FileText, X } from 'lucide-react';
import { API_BASE, DEFAULT_TASK, AppNav } from '../shared';

/* ── File type helpers ─────────────────────────────────────────────────────── */

// Only .md uploads are wired up end-to-end today (see POST /api/file-extractions,
// which writes the raw content straight into the target repo's docs/input/ tree).
// pdf/xlsx/txt extraction is not implemented yet, so they are left out of the
// picker rather than accepted and then rejected by the backend.
const ACCEPTED_TYPES = {
  'text/markdown': { label: 'MD', className: 'chip-md' },
};
const ACCEPTED_EXT = '.md';

function fileTypeMeta(file) {
  return ACCEPTED_TYPES[file.type] || { label: 'MD', className: 'chip-md' };
}

function fmtSize(bytes) {
  if (bytes < 1024)       return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function FileIcon() {
  return <FileText size={13} aria-hidden />;
}

/* ── FileUploadZone ─────────────────────────────────────────────────────────── */

const DOC_TYPES = [
  { value: 'requirement',     label: 'Requirement' },
  { value: 'change-request',  label: 'Change Request' },
  { value: 'architecture',    label: 'Technical Architecture' },
];

function FileUploadZone({ files, onChange, docType, onDocTypeChange }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const addFiles = useCallback((incoming) => {
    const valid = Array.from(incoming).filter((f) => /\.md$/i.test(f.name));
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
        <span>Attachments <small className="uploadLabel-hint">Markdown (.md) only</small></span>
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

      {files.length > 0 && (
        <label className="docTypeSelect">
          <span>Document type</span>
          <select value={docType} onChange={(e) => onDocTypeChange(e.target.value)}>
            {DOC_TYPES.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </label>
      )}

      {/* file chips */}
      {files.length > 0 && (
        <ul className="fileChipList" aria-label="Attached files">
          {files.map((file, i) => {
            const meta = fileTypeMeta(file);
            return (
              <li key={`${file.name}-${file.size}`} className="fileChip">
                <FileIcon />
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

/* ── Upload files before the run is created ──────────────────────────────────
 * Files are uploaded standalone (no run_id yet) so their content can be
 * validated and stored first; the returned extraction ids are then attached
 * when the harness run is created, which writes them into the target repo
 * before the harness subprocess starts. Uploading after the run already
 * exists would race the harness's H1-context phase, which reads the target
 * repo's docs/input/ tree almost immediately. */

async function uploadFiles(files, docType) {
  if (!files.length) return [];
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  form.append('doc_type', docType);
  const res = await fetch(`${API_BASE}/api/file-extractions`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Upload failed (${res.status})`);
  }
  const payload = await res.json();
  return payload.files.map((f) => f.id);
}

/* ── LaunchForm ─────────────────────────────────────────────────────────────── */

function LaunchForm({ onRunStarted }) {
  const [feature,  setFeature]  = useState(DEFAULT_TASK);
  const [provider, setProvider] = useState('claude');
  const [files,    setFiles]    = useState([]);
  const [docType,  setDocType]  = useState('requirement');
  const [starting, setStarting] = useState(false);
  const [error,    setError]    = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setStarting(true);
    setError('');
    try {
      const extractionIds = await uploadFiles(files, docType);
      const res = await fetch(`${API_BASE}/api/harness-runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feature, provider, mode: 'expanded', extraction_ids: extractionIds }),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const payload = await res.json();
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

        <FileUploadZone files={files} onChange={setFiles} docType={docType} onDocTypeChange={setDocType} />

        <div className="launchCard-row2">
          <label>
            <span>Provider</span>
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <option value="codex">Codex</option>
              <option value="claude">Claude Code</option>
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
