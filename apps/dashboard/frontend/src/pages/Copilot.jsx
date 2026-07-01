import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  Bot,
  Check,
  Code2,
  FileCode2,
  FilePlus2,
  LayoutDashboard,
  PanelLeft,
  Plus,
  Send,
  X,
} from 'lucide-react';
import { API_BASE, StatusPill, relativeTime } from '../shared';

const UPLOAD_TARGETS = [
  { value: 'frontend/uploads', label: 'Frontend' },
  { value: 'backend/uploads', label: 'Backend' },
  { value: 'apps/frontend/uploads', label: 'App Frontend' },
  { value: 'apps/backend/uploads', label: 'App Backend' },
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
      body: 'Send a prompt or upload a file to start a harness-managed code chat.',
      state: 'done',
    }];
  }

  const items = [
    {
      type: 'tool',
      title: 'Harness code-chat',
      body: 'Delegated generation, validation, and repair to packages/ai-harness.',
      state: 'done',
    },
    {
      type: 'thinking',
      title: busy ? 'Thinking' : 'Request analysis',
      body: session.reasoning_summary || session.plan?.summary || 'Analyzing request and project shape.',
      state: busy ? 'active' : 'done',
      steps: session.assumptions || session.plan?.steps || [],
    },
  ];

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
      title: 'Uploaded files',
      body: session.requested_files.map((file) => file.path).join('\n'),
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

  useEffect(() => {
    if (changes[0]?.path && !changes.some((change) => change.path === selectedPath)) {
      setSelectedPath(changes[0].path);
    }
  }, [changes, selectedPath]);

  if (!selected) {
    return (
      <section className="ccCodePane">
        <header><span>Source preview</span></header>
        <div className="ccCodeEmpty">
          {busy ? <Activity size={18} className="spin" /> : <Code2 size={18} />}
          <span>{busy ? 'Waiting for generated code' : 'No generated code yet'}</span>
        </div>
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
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadedContent, setUploadedContent] = useState('');
  const [uploadTarget, setUploadTarget] = useState(UPLOAD_TARGETS[0].value);
  const [fileInstructions, setFileInstructions] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0].value);
  const [status, setStatus] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const streamRef = useRef(null);

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

  async function handleUploadChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    try {
      setUploadedContent(await readFileAsText(file));
      setUploadedFile(file);
      setShowUpload(true);
    } catch (err) {
      setUploadedFile(null);
      setUploadedContent('');
      setError(err.message || 'Unable to read uploaded file');
    } finally {
      e.target.value = '';
    }
  }

  async function submitPrompt(e) {
    e.preventDefault();
    const cleanPrompt = prompt.trim();
    const uploadedPath = uploadedFile ? `${uploadTarget}/${uploadedFile.name}` : '';
    if (!cleanPrompt && !uploadedPath) return;

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
    const requestedFiles = uploadedFile ? [{
      path: uploadedPath,
      action: 'create',
      instructions: fileInstructions.trim(),
      content: uploadedContent,
    }] : [];

    const workingSession = {
      id: 'working',
      prompt: effectivePrompt || `Apply uploaded file ${uploadedFile?.name || ''}`,
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
          target: 'okr-ghcp',
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
      setUploadedFile(null);
      setUploadedContent('');
      setFileInstructions('');
      setShowUpload(false);
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
            <span>Harness managed</span>
            <h1>Copilot Code Workbench</h1>
          </div>
          <StatusPill status={activeSession?.status || (busy ? 'planning' : 'idle')} />
        </header>

        {error && <div className="ccError">{error}</div>}

        <section className="ccWorkbench">
          <ActivityLog session={activeSession} busy={busy} />
          <CodeViewer session={activeSession} busy={busy} />
        </section>

        <form className="ccComposer" onSubmit={submitPrompt}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={activeSession?.status === 'clarification_needed' ? 'Answer the questions so code can be generated' : 'Ask for a runnable source change'}
            rows={3}
          />

          {showUpload && (
            <div className="ccUploadPanel">
              <label className="ccUploadDrop">
                <FilePlus2 size={17} />
                <span>{uploadedFile ? uploadedFile.name : 'Upload source file'}</span>
                <small>{uploadedFile ? `${Math.ceil(uploadedFile.size / 1024)} KB` : 'Text/code files'}</small>
                <input type="file" onChange={handleUploadChange} />
              </label>
              <div className="ccUploadTargets" role="group" aria-label="Upload destination">
                {UPLOAD_TARGETS.map((target) => (
                  <button
                    key={target.value}
                    type="button"
                    className={uploadTarget === target.value ? 'active' : ''}
                    onClick={() => setUploadTarget(target.value)}
                  >
                    {target.label}
                  </button>
                ))}
              </div>
              <input
                type="text"
                value={fileInstructions}
                onChange={(e) => setFileInstructions(e.target.value)}
                placeholder="Optional instruction for uploaded file"
              />
              {uploadedFile && (
                <code className="ccUploadPath">{uploadTarget}/{uploadedFile.name}</code>
              )}
            </div>
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
            <button
              type="button"
              className={`ccIconButton${showUpload ? ' active' : ''}`}
              onClick={() => setShowUpload((value) => !value)}
              aria-label="Toggle upload"
            >
              <FilePlus2 size={17} />
            </button>
            <button type="submit" className="ccSendButton" disabled={busy || (!prompt.trim() && !uploadedFile)}>
              {busy ? <Activity size={16} className="spin" /> : <Send size={16} />}
              Send
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
