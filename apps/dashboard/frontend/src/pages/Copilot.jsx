import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  Bot,
  Check,
  Code2,
  File,
  FileCode2,
  FileText,
  Image as ImageIcon,
  LayoutDashboard,
  Plus,
  Send,
  ShieldAlert,
  X,
} from 'lucide-react';
import { API_BASE, StatusPill, relativeTime } from '../shared';

const UPLOAD_TARGETS = [
  { value: 'docs/sdlc/current/uploads', label: 'Context', kind: 'context' },
  { value: 'frontend/uploads', label: 'Frontend source', kind: 'source' },
  { value: 'backend/uploads', label: 'Backend source', kind: 'source' },
  { value: 'apps/frontend/uploads', label: 'App Frontend source', kind: 'source' },
  { value: 'apps/backend/uploads', label: 'App Backend source', kind: 'source' },
];

const MODEL_OPTIONS = [
  { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' },
  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
  { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner' },
];

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error || new Error('Unable to read file'));
    reader.readAsText(file);
  });
}

function formatFileSize(size) {
  if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.ceil(size / 1024))} KB`;
}

function formatTokens(count) {
  if (!count) return '0';
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K`;
  return String(count);
}

function fileId(file) {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

function uploadType(name, type = '') {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (type.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) {
    return { label: 'Image', icon: ImageIcon, tone: 'image' };
  }
  if (ext === 'pdf') return { label: 'Pdf', icon: FileText, tone: 'pdf' };
  if (['doc', 'docx'].includes(ext)) return { label: 'Doc', icon: FileText, tone: 'doc' };
  if (['md', 'txt'].includes(ext)) return { label: 'Text', icon: FileText, tone: 'text' };
  if (['js', 'jsx', 'ts', 'tsx', 'py', 'css', 'html', 'json', 'yaml', 'yml'].includes(ext)) {
    return { label: ext.toUpperCase(), icon: FileCode2, tone: 'code' };
  }
  return { label: ext ? ext.toUpperCase() : 'File', icon: File, tone: 'file' };
}

function UploadFileChip({ file, onRemove }) {
  const meta = uploadType(file.name, file.type);
  const Icon = meta.icon;

  return (
    <div className="ccUploadFile">
      {file.previewUrl ? (
        <img src={file.previewUrl} alt="" />
      ) : (
        <span className={`ccUploadFileIcon ccUploadFileIcon--${meta.tone}`}>
          <Icon size={18} />
        </span>
      )}
      <div>
        <strong>{file.name}</strong>
        <small>{meta.label} · {formatFileSize(file.size)}</small>
      </div>
      <button type="button" onClick={onRemove} aria-label={`Remove ${file.name}`}>
        <X size={14} />
      </button>
    </div>
  );
}

function SessionRow({ session, active, onSelect }) {
  return (
    <button
      type="button"
      className={`ccSessionRow${active ? ' ccSessionRow--active' : ''}`}
      onClick={() => onSelect(session)}
    >
      <span>{session.prompt?.slice(0, 52) || session.id}</span>
      <small>{relativeTime(session.created_at)} · {session.status}</small>
    </button>
  );
}

function activityItems(session, busy) {
  if (!session) {
    return [{
      type: 'tool',
      title: 'Waiting for request',
      body: 'Send a prompt or upload a file to start a full SDLC run in HARNESS_COPILOT.',
      state: 'done',
    }];
  }

  const items = [
    {
      type: 'tool',
      title: 'HARNESS_COPILOT target',
      body: `Generated source and SDLC artifacts are written under ${session.target_repo || 'HARNESS_COPILOT'}.`,
      state: 'done',
    },
  ];

  if (session.guard?.status === 'blocked' || session.status === 'blocked') {
    items.push({
      type: 'error',
      title: 'Security harness',
      body: session.guard?.message || session.error || 'Request blocked by Copilot security guard.',
      state: 'error',
      steps: session.guard?.reasons || [],
    });
    return items;
  }

  if (session.sdlc_phases?.length) {
    const failed = session.sdlc_phases.some((phase) => phase.status === 'error');
    const active = session.sdlc_phases.some((phase) => phase.status === 'running');
    const byPhase = session.token_usage?.by_phase || {};
    items.push({
      type: 'thinking',
      title: 'SDLC pipeline',
      body: session.reasoning_summary || session.plan?.summary || 'Running AINative-style gated phases with DeepSeek.',
      state: failed ? 'error' : active || busy ? 'active' : 'done',
      steps: session.sdlc_phases.map((phase) => {
        const marker = phase.status === 'done' ? 'done' : phase.status === 'running' ? 'running' : phase.status === 'error' ? 'error' : 'pending';
        const phaseTokens = byPhase[phase.id];
        const tokenLabel = phaseTokens ? ` · ${formatTokens(phaseTokens.total_tokens)} tokens` : '';
        return `${marker} · ${phase.name}${phase.summary ? ` · ${phase.summary}` : ''}${tokenLabel}`;
      }),
    });
  } else {
    items.push({
      type: 'thinking',
      title: busy ? 'Thinking' : 'Request analysis',
      body: session.reasoning_summary || session.plan?.summary || 'Analyzing request and project shape.',
      state: busy ? 'active' : 'done',
      steps: session.assumptions || session.plan?.steps || [],
    });
  }

  if (session.clarification?.questions?.length) {
    items.push({
      type: 'thinking',
      title: 'Needs clarification',
      body: 'Answer these questions in the composer before code is generated.',
      state: 'active',
      steps: session.clarification.questions,
    });
  }

  if (session.requested_files?.length) {
    items.push({
      type: 'tool',
      title: 'Uploaded context/files',
      body: session.requested_files.map((file) => `${file.kind || 'context'} · ${file.path}`).join('\n'),
      state: 'done',
    });
  }

  if (session.changes?.length) {
    items.push({
      type: 'edit',
      title: `Generated ${session.changes.length} file change${session.changes.length === 1 ? '' : 's'}`,
      body: session.changes.map((change) => `${change.action} ${change.path}`).join('\n'),
      state: 'done',
    });
  }

  if (session.validation) {
    const failed = (session.validation.checks || []).filter((check) => check.return_code !== 0);
    items.push({
      type: session.validation.status === 'pass' ? 'apply' : 'tool',
      title:
        session.validation.status === 'pass'
          ? 'Validation passed'
          : session.validation.status === 'fail'
            ? 'Validation failed'
            : 'Validation skipped',
      body: [
        session.validation.summary,
        ...failed.map((check) => `$ ${check.command}\n${check.output || ''}`),
      ].filter(Boolean).join('\n\n'),
      state: session.validation.status === 'fail' ? 'error' : 'done',
    });
  }

  if (session.repair_attempts?.length) {
    session.repair_attempts.forEach((attempt) => {
      items.push({
        type: 'edit',
        title: `Repair attempt ${attempt.attempt}`,
        body: [
          `${attempt.applied_files?.length || 0} file${attempt.applied_files?.length === 1 ? '' : 's'} updated.`,
          attempt.validation?.summary,
        ].filter(Boolean).join('\n'),
        state: attempt.validation?.status === 'fail' ? 'error' : 'done',
      });
    });
  }

  if (session.error) {
    items.push({ type: 'error', title: 'Failed', body: session.error, state: 'error' });
  }

  if (session.token_usage?.total_tokens > 0) {
    const u = session.token_usage;
    items.push({
      type: 'tool',
      title: `Token usage · ${formatTokens(u.total_tokens)} total`,
      body: `${u.calls} API call${u.calls === 1 ? '' : 's'} · ${formatTokens(u.prompt_tokens)} prompt · ${formatTokens(u.completion_tokens)} completion`,
      state: 'done',
      steps: Object.entries(u.by_phase || {}).map(
        ([phase, p]) => `${phase}: ${formatTokens(p.total_tokens)} tokens (${p.calls} call${p.calls === 1 ? '' : 's'})`
      ),
    });
  }

  return items;
}

function ActivityIcon({ type, state }) {
  if (state === 'active') return <Activity size={15} className="spin" />;
  if (state === 'error') return <X size={15} />;
  if (type === 'thinking') return <Bot size={15} />;
  if (type === 'edit') return <FileCode2 size={15} />;
  if (type === 'apply') return <Check size={15} />;
  return <Code2 size={15} />;
}

function ActivityLog({ session, busy }) {
  return (
    <div className="ccLog">
      {activityItems(session, busy).map((item, index) => (
        <article key={`${item.title}-${index}`} className={`ccLogItem ccLogItem--${item.state}`}>
          <div className="ccLogIcon"><ActivityIcon type={item.type} state={item.state} /></div>
          <div className="ccLogBody">
            <h3>{item.title}{item.state === 'active' && <span className="thinkingDots" aria-hidden />}</h3>
            <p>{item.body}</p>
            {item.steps?.length > 0 && (
              <ul>{item.steps.map((step) => <li key={step}>{step}</li>)}</ul>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}

function lineClass(line) {
  if (line.startsWith('+') && !line.startsWith('+++')) return 'lineAdd';
  if (line.startsWith('-') && !line.startsWith('---')) return 'lineDel';
  if (line.startsWith('@@')) return 'lineMeta';
  if (line.startsWith('diff ') || line.startsWith('---') || line.startsWith('+++')) return 'lineHeader';
  return '';
}

function CodeViewer({ session, busy }) {
  const changes = session?.changes || [];
  const [selectedPath, setSelectedPath] = useState('');
  const [mode, setMode] = useState('source');
  const selected = changes.find((change) => change.path === selectedPath) || changes[0];
  const guardMessage = session?.guard?.status === 'blocked' || session?.status === 'blocked'
    ? session?.guard?.message || session?.error || 'Request blocked by Copilot security guard.'
    : '';

  useEffect(() => {
    if (changes[0]?.path && !changes.some((change) => change.path === selectedPath)) {
      setSelectedPath(changes[0].path);
    }
  }, [changes, selectedPath]);

  if (!selected) {
    return (
      <section className="ccCodePane">
        <header><span>Source preview</span></header>
        {guardMessage ? (
          <div className="ccGuardNotice">
            <span><ShieldAlert size={22} /></span>
            <strong>Security harness</strong>
            <p>{guardMessage}</p>
          </div>
        ) : (
          <div className="ccCodeEmpty">
            {busy ? <Activity size={18} className="spin" /> : <Code2 size={18} />}
            <span>{busy ? 'Waiting for generated code' : 'No generated code yet'}</span>
          </div>
        )}
      </section>
    );
  }

  const sourceLines = String(selected.content || '').split('\n');
  const diffLines = String(session.diff || '').split('\n');
  const lines = mode === 'source' ? sourceLines : diffLines;
  const added = diffLines.filter((line) => line.startsWith('+') && !line.startsWith('+++')).length;
  const removed = diffLines.filter((line) => line.startsWith('-') && !line.startsWith('---')).length;

  return (
    <section className="ccCodePane">
      <header>
        <div className="ccFileTabs">
          {changes.map((change) => (
            <button
              key={change.path}
              type="button"
              className={change.path === selected.path ? 'active' : ''}
              onClick={() => setSelectedPath(change.path)}
            >
              <FileCode2 size={14} />
              <span>{change.path}</span>
            </button>
          ))}
        </div>
        <div className="ccCodeStats"><span>+{added}</span><span>-{removed}</span></div>
      </header>

      <div className="ccCodeToolbar">
        <div>
          <strong>{selected.action}</strong>
          <code>{selected.path}</code>
        </div>
        <div className="ccCodeMode">
          <button type="button" className={mode === 'source' ? 'active' : ''} onClick={() => setMode('source')}>Source</button>
          <button type="button" className={mode === 'diff' ? 'active' : ''} onClick={() => setMode('diff')}>Diff</button>
        </div>
      </div>

      <pre className="ccCodeBlock">
        {lines.map((line, index) => (
          <span key={`${mode}-${index}`} className={mode === 'diff' ? lineClass(line) : ''}>
            <em>{String(index + 1).padStart(3, ' ')}</em>
            <code>{line || ' '}</code>
          </span>
        ))}
      </pre>
    </section>
  );
}

export default function CopilotPage() {
  const [prompt, setPrompt] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const uploadTarget = UPLOAD_TARGETS[0].value;
  const [draggingUpload, setDraggingUpload] = useState(false);
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0].value);
  const [status, setStatus] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);

  async function loadStatus() {
    try {
      const res = await fetch(`${API_BASE}/api/copilot/status`);
      if (res.ok) setStatus(await res.json());
    } catch {}
  }

  async function loadSessions() {
    try {
      const res = await fetch(`${API_BASE}/api/copilot/sessions`);
      if (!res.ok) return;
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch {}
  }

  useEffect(() => {
    loadStatus();
    loadSessions();
    return () => streamRef.current?.close();
  }, []);

  function connectSessionStream(sessionId) {
    streamRef.current?.close();
    const source = new EventSource(`${API_BASE}/api/copilot/sessions/${sessionId}/events`);
    streamRef.current = source;

    const updateSession = (event) => {
      const next = JSON.parse(event.data);
      setActiveSession(next);
      setSessions((prev) => [next, ...prev.filter((item) => item.id !== next.id)]);
    };

    source.addEventListener('session', updateSession);
    source.addEventListener('done', (event) => {
      updateSession(event);
      setBusy(false);
      source.close();
      if (streamRef.current === source) streamRef.current = null;
    });
    source.onerror = () => {
      setBusy(false);
      source.close();
      if (streamRef.current === source) streamRef.current = null;
    };
  }

  async function addUploadFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    setError('');
    try {
      const nextFiles = await Promise.all(files.map(async (file) => ({
        id: fileId(file),
        name: file.name,
        size: file.size,
        type: file.type,
        previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : '',
        content: await readFileAsText(file),
      })));
      setUploadedFiles((current) => {
        const byId = new Map(current.map((file) => [file.id, file]));
        nextFiles.forEach((file) => byId.set(file.id, file));
        return Array.from(byId.values()).slice(0, 10);
      });
    } catch (err) {
      setError(err.message || 'Unable to read uploaded files');
    }
  }

  async function handleUploadChange(e) {
    await addUploadFiles(e.target.files);
    e.target.value = '';
  }

  function removeUploadFile(id) {
    setUploadedFiles((current) => current.filter((file) => file.id !== id));
  }

  function handleUploadDrop(e) {
    e.preventDefault();
    setDraggingUpload(false);
    addUploadFiles(e.dataTransfer.files);
  }

  async function submitPrompt(e) {
    e.preventDefault();
    const cleanPrompt = prompt.trim();
    const selectedUploadTarget = UPLOAD_TARGETS[0];
    if (!cleanPrompt && !uploadedFiles.length) return;

    const clarificationPrefix = activeSession?.status === 'clarification_needed'
      ? [
          'Original request:',
          activeSession.prompt,
          '',
          'Clarification questions:',
          ...(activeSession.clarification?.questions || []).map((question, index) => `${index + 1}. ${question}`),
          '',
          'User answers / additional details:',
        ].join('\n')
      : '';
    const effectivePrompt = clarificationPrefix
      ? `${clarificationPrefix}\n${cleanPrompt || '(no extra text)'}`
      : cleanPrompt;
    const requestedFiles = uploadedFiles.map((file) => ({
      path: `${uploadTarget}/${file.name}`,
      kind: selectedUploadTarget.kind,
      action: 'create',
      instructions: '',
      content: file.content,
    }));

    const workingSession = {
      id: 'working',
      prompt: effectivePrompt || `Use uploaded file context: ${uploadedFiles.map((file) => file.name).join(', ')}`,
      model: selectedModel,
      status: 'planning',
      requested_files: requestedFiles,
      changes: [],
      diff: '',
      applied_files: [],
      created_at: Date.now() / 1000,
    };
    setBusy(true);
    setError('');
    setActiveSession(workingSession);

    try {
      const res = await fetch(`${API_BASE}/api/copilot/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: workingSession.prompt,
          target: 'harness-copilot',
          model: selectedModel,
          requested_files: requestedFiles,
          auto_apply: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `API ${res.status}`);
      setActiveSession(data);
      setSessions((prev) => [data, ...prev.filter((item) => item.id !== data.id)]);
      connectSessionStream(data.id);
      setPrompt('');
      setUploadedFiles([]);
    } catch (err) {
      setError(err.message || 'Failed to start code session');
      setBusy(false);
    }
  }

  return (
    <div className="ccPage">
      <aside className="ccSidebar">
        <div className="ccBrand">
          <span className="copilotMark" aria-hidden />
          <div>
            <strong>Code Chat</strong>
            <small>{status?.configured ? `${MODEL_OPTIONS.find((model) => model.value === selectedModel)?.label || selectedModel} ready` : 'DeepSeek key missing'}</small>
          </div>
        </div>
        <nav className="ccNav">
          <a href="#/"><LayoutDashboard size={16} /> Dashboard</a>
          <button type="button" onClick={() => { setActiveSession(null); setPrompt(''); }}>
            <Plus size={16} /> New chat
          </button>
        </nav>
        <div className="ccSessions">
          <span>Sessions</span>
          {sessions.length ? sessions.map((session) => (
            <SessionRow
              key={session.id}
              session={session}
              active={session.id === activeSession?.id}
              onSelect={setActiveSession}
            />
          )) : <small className="ccEmptyText">No sessions yet</small>}
        </div>
      </aside>

      <main className="ccMain">
        <header className="ccHeader">
          <div>
            <span>{status?.target_repo || 'HARNESS_COPILOT'}</span>
            <h1>Copilot Code Workbench</h1>
          </div>
          <StatusPill status={activeSession?.status || (busy ? 'planning' : 'idle')} />
        </header>

        {error && <div className="ccError">{error}</div>}

        <section className="ccWorkbench">
          <ActivityLog session={activeSession} busy={busy} />
          <CodeViewer session={activeSession} busy={busy} />
        </section>

        <form
          className="ccComposer"
          onSubmit={submitPrompt}
          onDragOver={(e) => {
            e.preventDefault();
            setDraggingUpload(true);
          }}
          onDragLeave={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) setDraggingUpload(false);
          }}
          onDrop={handleUploadDrop}
        >
          <div className={`ccChatInput${uploadedFiles.length ? ' ccChatInput--attached' : ''}`}>
            {uploadedFiles.length > 0 && (
              <div className="ccChatAttachments">
                {uploadedFiles.map((file) => (
                  <UploadFileChip
                    key={file.id}
                    file={file}
                    onRemove={() => removeUploadFile(file.id)}
                  />
                ))}
              </div>
            )}

            <div className="ccChatInputRow">
              <button
                type="button"
                className="ccChatUploadButton"
                onClick={() => {
                  fileInputRef.current?.click();
                }}
                aria-label="Attach files"
              >
                ↑
              </button>
              <input ref={fileInputRef} type="file" multiple onChange={handleUploadChange} />

              <div className="ccChatTextWrap">
                {!prompt && (
                  <span className="ccChatPlaceholder">
                    {activeSession?.status === 'clarification_needed' ? (
                      'Answer the questions so code can be generated'
                    ) : (
                      <>
                        Type <kbd>/</kbd> for commands
                      </>
                    )}
                  </span>
                )}
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={1}
                  aria-label="Copilot prompt"
                />
              </div>

              <button type="button" className="ccVoiceButton" aria-label="Voice input">
                <span />
                <span />
                <span />
                <span />
              </button>

              <button type="submit" className="ccSendOrb" disabled={busy || (!prompt.trim() && !uploadedFiles.length)} aria-label="Send">
                {busy ? <Activity size={17} className="spin" /> : <Send size={18} />}
              </button>
            </div>
          </div>

          {draggingUpload && (
            <div className="ccDropHint">Drop files to attach them as context</div>
          )}

          <div className="ccComposerFooter">
            <label className="ccModelSelect">
              <span>Model</span>
              <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
                {MODEL_OPTIONS.map((model) => (
                  <option key={model.value} value={model.value}>{model.label}</option>
                ))}
              </select>
            </label>
          </div>
        </form>
      </main>
    </div>
  );
}
