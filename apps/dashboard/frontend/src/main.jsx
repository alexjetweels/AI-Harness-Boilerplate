import React from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  Bot,
  CheckCircle2,
  CircleAlert,
  FileText,
  Play,
  Square,
  Terminal,
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || '';

const DEFAULT_TASK =
  'Build a browser Todo UI for the demo app with add, complete, delete, and persistent tasks';

function statusLabel(status) {
  return String(status || 'pending').replaceAll('_', ' ');
}

function phaseState(phase, currentPhase, runStatus) {
  if (phase.status === 'done') return 'done';
  if (phase.status === 'failed') return 'failed';
  if (phase.name === currentPhase && runStatus === 'running') return 'current';
  return 'pending';
}

function useHarnessRun(activeRunId) {
  const [run, setRun] = React.useState(null);
  const [error, setError] = React.useState('');

  const load = React.useCallback(async () => {
    const url = activeRunId
      ? `${API_BASE}/api/harness-runs/${activeRunId}`
      : `${API_BASE}/api/harness-runs/latest`;
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`API returned ${response.status}`);
      const payload = await response.json();
      setRun(payload.run === undefined ? payload : payload.run);
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to load harness run');
    }
  }, [activeRunId]);

  React.useEffect(() => {
    load();
    const id = window.setInterval(load, 2500);
    return () => window.clearInterval(id);
  }, [load]);

  return { run, error, reload: load };
}

function App() {
  const [activeRunId, setActiveRunId] = React.useState('');
  const { run, error, reload } = useHarnessRun(activeRunId);
  const [feature, setFeature] = React.useState(DEFAULT_TASK);
  const [provider, setProvider] = React.useState('codex');
  const [starting, setStarting] = React.useState(false);
  const [stopping, setStopping] = React.useState(false);

  async function startRun(event) {
    event.preventDefault();
    setStarting(true);
    try {
      const response = await fetch(`${API_BASE}/api/harness-runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feature,
          provider,
          target: 'todo-app',
          tech_stack: 'Node.js Todo demo target',
        }),
      });
      if (!response.ok) throw new Error(`API returned ${response.status}`);
      const payload = await response.json();
      setActiveRunId(payload.id);
      await reload();
    } finally {
      setStarting(false);
    }
  }

  async function stopRun() {
    if (!run?.id) return;
    setStopping(true);
    try {
      await fetch(`${API_BASE}/api/harness-runs/${run.id}/stop`, { method: 'POST' });
      await reload();
    } finally {
      setStopping(false);
    }
  }

  return (
    <main className='shell'>
      <section className='workspace'>
        <header className='topbar'>
          <div>
            <h1>AI SDLC Harness</h1>
            <p>Start a task from the dashboard and let the harness execute against the Todo demo target.</p>
          </div>
          <StatusPill status={run?.status || 'idle'} />
        </header>

        <TaskLauncher
          feature={feature}
          setFeature={setFeature}
          provider={provider}
          setProvider={setProvider}
          startRun={startRun}
          stopRun={stopRun}
          starting={starting}
          stopping={stopping}
          run={run}
        />

        {error ? <div className='errorLine'>{error}</div> : null}

        <div className='contentGrid'>
          <PhasePanel run={run} />
          <OutputPanel run={run} />
        </div>
      </section>
    </main>
  );
}

function TaskLauncher({
  feature,
  setFeature,
  provider,
  setProvider,
  startRun,
  stopRun,
  starting,
  stopping,
  run,
}) {
  const canStop = run?.status === 'running' || run?.status === 'queued';
  return (
    <section className='launcher'>
      <form onSubmit={startRun}>
        <label>
          <span>Task</span>
          <textarea
            value={feature}
            onChange={(event) => setFeature(event.target.value)}
            rows={3}
          />
        </label>
        <div className='controlRow'>
          <label>
            <span>Provider</span>
            <select value={provider} onChange={(event) => setProvider(event.target.value)}>
              <option value='codex'>Codex</option>
              <option value='claude'>Claude Code</option>
            </select>
          </label>
          <label>
            <span>Target</span>
            <select value='todo-app' disabled>
              <option>Todo App Demo</option>
            </select>
          </label>
          <button className='primaryButton' type='submit' disabled={starting || !feature.trim()}>
            {starting ? <Activity className='spin' size={16} /> : <Play size={16} />}
            Start task
          </button>
          <button className='secondaryButton' type='button' disabled={!canStop || stopping} onClick={stopRun}>
            <Square size={16} />
            Stop
          </button>
        </div>
      </form>
    </section>
  );
}

function PhasePanel({ run }) {
  const phases = run?.phases || [];
  return (
    <section className='panel phasePanel'>
      <div className='panelHeader'>
        <h2>Execution Flow</h2>
        <span>{run?.id || 'no run yet'}</span>
      </div>
      <div className='phaseList'>
        {phases.length === 0 ? (
          <EmptyState icon={<Bot size={22} />} text='Start a task to create a harness run.' />
        ) : (
          phases.map((phase, index) => (
            <PhaseItem
              key={phase.name}
              index={index + 1}
              phase={phase}
              state={phaseState(phase, run.current_phase, run.status)}
            />
          ))
        )}
      </div>
    </section>
  );
}

function PhaseItem({ index, phase, state }) {
  const icon =
    state === 'done' ? (
      <CheckCircle2 size={17} />
    ) : state === 'failed' ? (
      <CircleAlert size={17} />
    ) : state === 'current' ? (
      <Activity className='spin' size={17} />
    ) : (
      <span className='phaseNumber'>{index}</span>
    );

  return (
    <article className={`phaseItem ${state}`}>
      <div className='phaseIcon'>{icon}</div>
      <div>
        <strong>{phase.name}</strong>
        <span>
          {statusLabel(phase.status)}
          {phase.gate ? ` / gate ${phase.gate}` : ''}
          {phase.attempts ? ` / ${phase.attempts} attempt(s)` : ''}
        </span>
      </div>
    </article>
  );
}

function OutputPanel({ run }) {
  return (
    <section className='panel outputPanel'>
      <div className='panelHeader'>
        <h2>Run Output</h2>
        <span>{run?.provider || 'provider'}</span>
      </div>

      <div className='runSummary'>
        <SummaryItem label='Target' value={run?.target || 'todo-app'} />
        <SummaryItem label='Cost' value={`$${Number(run?.cost_usd || 0).toFixed(4)}`} />
        <SummaryItem label='Return' value={run?.return_code ?? '-'} />
      </div>

      <div className='artifactBlock'>
        <h3>
          <FileText size={16} />
          Artifacts
        </h3>
        {run?.artifacts?.length ? (
          <ul>
            {run.artifacts.map((artifact) => (
              <li key={artifact.path}>
                <span>{artifact.name}</span>
                <small>{artifact.path}</small>
              </li>
            ))}
          </ul>
        ) : (
          <p>No SDLC artifacts yet.</p>
        )}
      </div>

      <div className='logBlock'>
        <h3>
          <Terminal size={16} />
          Log Tail
        </h3>
        <pre>{run?.log_tail?.length ? run.log_tail.join('\n') : 'Waiting for harness output...'}</pre>
      </div>
    </section>
  );
}

function SummaryItem({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusPill({ status }) {
  return <span className={`statusPill ${status}`}>{statusLabel(status)}</span>;
}

function EmptyState({ icon, text }) {
  return (
    <div className='emptyState'>
      {icon}
      <span>{text}</span>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
