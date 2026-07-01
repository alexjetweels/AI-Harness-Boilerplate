import React, { useState, useMemo, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Activity, ArrowLeft, ChevronLeft, RotateCcw, Square } from 'lucide-react';
import {
  statusLabel,
  useHarnessRun,
  useRunHistory,
  useGateOutcomes,
  StatusPill,
  PipelineFlow,
  PhaseDetailPanel,
  RunOutputPanel,
} from '../shared';

/* ── Pipeline header ─────────────────────────────────────────────────────── */

function PipelineHeader({
  run,
  onBack,
  onStop,
  stopping,
  onRetry,
  retrying,
  retryProvider,
  onRetryProviderChange,
}) {
  const canStop = run?.status === 'running' || run?.status === 'queued';
  const canRetry = ['failed', 'escalated', 'stopped'].includes(run?.status);
  const doneCount = (run?.phases || []).filter((p) => p.status === 'done').length;
  const totalCount = run?.phases?.length || 0;

  return (
    <header className="pipelinePageHeader">
      <button className="backBtn" onClick={onBack} aria-label="Back to dashboard">
        <ChevronLeft size={16} />
        Dashboard
      </button>

      <div className="pipelinePageHeader-divider" />

      <div className="pipelinePageHeader-run">
        <code className="pipelinePageHeader-id">{run?.id || '—'}</code>
        {run?.target && <span className="pipelinePageHeader-tag">{run.target}</span>}
        {run?.mode   && <span className="pipelinePageHeader-tag">{run.mode}</span>}
      </div>

      <StatusPill status={run?.status || 'idle'} />

      {run?.status === 'running' && run?.current_phase && (
        <span className="pipelinePageHeader-current">
          <Activity size={11} className="spin" />
          {run.current_phase}
        </span>
      )}

      <div className="pipelinePageHeader-spacer" />

      {totalCount > 0 && (
        <span className="pipelinePageHeader-progress">
          {doneCount}/{totalCount} phases
        </span>
      )}

      {run?.cost_usd > 0 && (
        <span className="pipelinePageHeader-cost">
          ${Number(run.cost_usd).toFixed(4)}
        </span>
      )}

      {canStop && (
        <button className="stopBtn" onClick={onStop} disabled={stopping}>
          <Square size={13} />
          Stop
        </button>
      )}

      {canRetry && (
        <div className="retryGroup">
          <select
            className="retryProviderSelect"
            value={retryProvider}
            onChange={(e) => onRetryProviderChange(e.target.value)}
            disabled={retrying}
            aria-label="Provider for retry"
          >
            <option value="">Same provider</option>
            <option value="claude">Claude Code</option>
            <option value="codex">Codex</option>
          </select>
          <button className="retryBtn" onClick={onRetry} disabled={retrying}>
            <RotateCcw size={13} />
            {retrying ? 'Retrying…' : 'Retry'}
          </button>
        </div>
      )}
    </header>
  );
}

/* ── Pipeline page ───────────────────────────────────────────────────────── */

export default function PipelinePage() {
  const { runId } = useParams();
  const navigate  = useNavigate();

  const { run, error, reload } = useHarnessRun(runId);
  const { phaseTimeline, events } = useRunHistory(runId);
  const gatesByPhase = useGateOutcomes(runId);

  const [selectedPhase, setSelectedPhase] = useState(null);
  const [stopping, setStopping] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [retryProvider, setRetryProvider] = useState('');

  const timelineMap = useMemo(() => {
    const map = {};
    for (const entry of phaseTimeline) {
      if (!map[entry.phase_name] || entry.attempt >= (map[entry.phase_name]?.attempt || 0)) {
        map[entry.phase_name] = entry;
      }
    }
    return map;
  }, [phaseTimeline]);

  const handlePhaseSelect = useCallback(
    (phaseId) => setSelectedPhase(phaseId),
    [],
  );

  async function stopRun() {
    if (!run?.id) return;
    setStopping(true);
    try {
      await fetch(`/api/harness-runs/${run.id}/stop`, { method: 'POST' });
      await reload();
    } finally {
      setStopping(false);
    }
  }

  async function retryRun() {
    if (!run?.id) return;
    setRetrying(true);
    try {
      await fetch(`/api/harness-runs/${run.id}/retry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: retryProvider || null }),
      });
      await reload();
    } finally {
      setRetrying(false);
    }
  }

  /* ── Not found ── */
  if (error) {
    return (
      <div className="pipelinePage pipelinePage--error">
        <header className="pipelinePageHeader">
          <button className="backBtn" onClick={() => navigate('/')}>
            <ChevronLeft size={16} />Dashboard
          </button>
        </header>
        <div className="pipelineError">
          <p className="pipelineError-msg">{error}</p>
          <button className="primaryButton" onClick={() => navigate('/')}>
            <ArrowLeft size={14} />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pipelinePage">
      <PipelineHeader
        run={run}
        onBack={() => navigate('/')}
        onStop={stopRun}
        stopping={stopping}
        onRetry={retryRun}
        retrying={retrying}
        retryProvider={retryProvider}
        onRetryProviderChange={setRetryProvider}
      />

      <div className="pipelinePageBody">
        {/* ── Left: breadcrumb bar ── */}
        <div className="pipelinePageLeft">
          <div className="pipelinePageTitle">
            <span className="pipelineSectionLabel">Execution Pipeline</span>
            <span className="pipelinePageHint">Click a step to inspect</span>
          </div>
          <div className="pipelineCanvasFull">
            <PipelineFlow
              run={run}
              timelineMap={timelineMap}
              selectedPhase={selectedPhase}
              onPhaseSelect={handlePhaseSelect}
            />
          </div>
        </div>

        {/* ── Right: detail panel ── */}
        {selectedPhase ? (
          <PhaseDetailPanel
            run={run}
            selectedPhase={selectedPhase}
            gatesByPhase={gatesByPhase}
            events={events}
            phaseTimeline={phaseTimeline}
            onClose={() => setSelectedPhase(null)}
          />
        ) : (
          <RunOutputPanel run={run} events={events} />
        )}
      </div>
    </div>
  );
}
