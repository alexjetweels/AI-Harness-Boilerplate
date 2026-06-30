/**
 * shared.jsx – constants, helpers, hooks, and UI components used by both pages.
 */
import React, { memo, useMemo, useCallback, useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Circle,
  Code2,
  Database,
  FileText,
  Layers,
  Search,
  Shield,
  Terminal,
  TestTube2,
  X,
} from 'lucide-react';

/* ── Config ──────────────────────────────────────────────────────────────── */

export const API_BASE = import.meta.env.VITE_API_BASE || '';
export const DEFAULT_TASK =
  'Build the OKR web application from the imported requirements, change requests, and technical architecture';

export const NODE_W = 252;
export const STEP    = 128;

/* ── Phase registry ──────────────────────────────────────────────────────── */

export const PHASE_META = {
  // ── H1 / H4 harness phases ──────────────────────────────────────────────
  'H1-context':             { label: 'Context Build',       layer: 'H1',   desc: 'Assemble deterministic context packet before any agent call', Icon: Database },
  'H4-context-security':    { label: 'Context Security',    layer: 'H4',   desc: 'Scan context payload for secrets & unsafe patterns',          Icon: Shield },
  'H4-generated-security':  { label: 'Generated Security',  layer: 'H4',   desc: 'Scan generated artifacts and source for secrets & OWASP issues', Icon: Shield },
  // ── IPA Doc Gen phases ──────────────────────────────────────────────────
  'system-srs':             { label: 'System SRS',          layer: 'SDLC', desc: 'Generate full system-wide requirements specification (okr.srsallsystem)', Icon: FileText },
  'srs':                    { label: 'SRS',                 layer: 'SDLC', desc: 'Software requirements specification per module (okr.srs)',    Icon: FileText },
  'basic-design':           { label: 'Basic Design',        layer: 'SDLC', desc: 'External design — high-level architecture decisions (okr.bd)', Icon: Layers },
  'detail-design':          { label: 'Detail Design',       layer: 'SDLC', desc: 'Internal design — component-level documentation (okr.dd)',    Icon: FileText },
  // ── Spec-Kit phases ──────────────────────────────────────────────────────
  'specify':                { label: 'Spec Creation',       layer: 'SDLC', desc: 'Feature spec via Spec-Kit (speckit.specify → spec.md)',        Icon: Code2 },
  'clarify':                { label: 'Clarify',             layer: 'SDLC', desc: 'Resolve all [NEEDS CLARIFICATION] markers autonomously',       Icon: Search },
  'plan':                   { label: 'Plan',                layer: 'SDLC', desc: 'Implementation plan + data-model + contracts (speckit.plan)',   Icon: Layers },
  'tasks':                  { label: 'Task Breakdown',      layer: 'SDLC', desc: 'Decompose plan into discrete executable tasks (speckit.tasks)', Icon: Activity },
  'implement':              { label: 'Implementation',      layer: 'SDLC', desc: 'AI-driven code generation with auto build & fix (speckit.implement)', Icon: Code2 },
  // ── Review phases ────────────────────────────────────────────────────────
  'review-spec':            { label: 'Spec Review',         layer: 'SDLC', desc: 'Validate spec.md quality & completeness (okr.reviewspec)',     Icon: Search },
  'review-plan':            { label: 'Plan Review',         layer: 'SDLC', desc: 'Validate plan.md conformance to spec (okr.reviewplan)',        Icon: Search },
  'review-code':            { label: 'Code Review',         layer: 'SDLC', desc: 'Code quality, DB data check, security (okr.reviewcode)',       Icon: Search },
  // ── Test phases ───────────────────────────────────────────────────────────
  'generate-tests':         { label: 'Generate Tests',      layer: 'SDLC', desc: 'Generate test cases from SRS/BD/DD (okr.testkit gen-testcases)', Icon: TestTube2 },
  'run-tests':              { label: 'Run Tests',           layer: 'SDLC', desc: 'Execute automated tests — BACK-TO-PLAN on fail (okr.testkit run-tests)', Icon: TestTube2 },
  // ── Final phase ───────────────────────────────────────────────────────────
  'verify-launch':          { label: 'Verify & Launch',     layer: 'H3',   desc: 'Final acceptance gate: build, test, docker compose up',        Icon: CheckCircle2 },
  // ── Boss-mode phase ───────────────────────────────────────────────────────
  'boss-pipeline':          { label: 'Boss Pipeline',       layer: 'SDLC', desc: 'Full 13-step orchestration via okr.bossbuiltin (boss mode)',   Icon: Activity },
  // ── Legacy / generic aliases ─────────────────────────────────────────────
  'analyze':                { label: 'Analysis',            layer: 'SDLC', desc: 'Cross-artifact consistency and dependency check',              Icon: Search },
  'test':                   { label: 'Testing',             layer: 'SDLC', desc: 'Test case generation and automated validation',               Icon: TestTube2 },
  'review':                 { label: 'Code Review',         layer: 'SDLC', desc: 'Automated quality, logic, and standards review',              Icon: Search },
  'security-review':        { label: 'Security Review',     layer: 'H4',   desc: 'Security vulnerability and OWASP audit',                      Icon: Shield },
  'verify':                 { label: 'Verify',              layer: 'H3',   desc: 'Final acceptance gate — deterministic pass/fail check',       Icon: CheckCircle2 },
};

export const DEFAULT_PIPELINE = [
  'H1-context', 'H4-context-security', 'system-srs', 'srs', 'basic-design',
  'specify', 'clarify', 'plan', 'tasks', 'analyze', 'detail-design',
  'implement', 'test', 'review', 'security-review', 'verify',
];

export const LAYER_STYLE = {
  H1:   { color: '#a78bfa', bg: 'rgba(139,92,246,0.15)',  border: 'rgba(139,92,246,0.45)' },
  H4:   { color: '#fbbf24', bg: 'rgba(245,158,11,0.13)',  border: 'rgba(245,158,11,0.4)' },
  H3:   { color: '#60a5fa', bg: 'rgba(59,130,246,0.13)',  border: 'rgba(59,130,246,0.45)' },
  SDLC: { color: '#65c6a5', bg: 'rgba(101,198,165,0.1)',  border: 'rgba(101,198,165,0.3)' },
};

export const EVENT_TYPE_LABELS = {
  run_created:        'INIT',
  phase_started:      'START',
  phase_done:         'DONE',
  gate_checked:       'GATE',
  claude_text:        'CLAUDE',
  claude_tool:        'TOOL',
  claude_tool_result: 'RESULT',
  claude_done:        'COST',
  claude_raw:         'RAW',
  escalated:          'ESCALATED',
};

/* ── Helpers ─────────────────────────────────────────────────────────────── */

export function statusLabel(s) {
  return String(s || 'pending').replaceAll('_', ' ');
}

export function phaseRunStatus(phaseData, phaseName, currentPhase, runStatus) {
  if (!phaseData) {
    return phaseName === currentPhase && runStatus === 'running' ? 'running' : 'pending';
  }
  if (phaseData.status === 'done') return phaseData.gate === 'fail' ? 'done-fail' : 'done';
  if (phaseData.status === 'failed') return 'failed';
  if (phaseName === currentPhase && runStatus === 'running') return 'running';
  return 'pending';
}

export function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(Number(ts) * 1000);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
}

export function relativeTime(ts) {
  if (!ts) return '—';
  const sec = Math.floor(Date.now() / 1000 - Number(ts));
  if (sec < 60)    return 'just now';
  if (sec < 3600)  return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
  return `${Math.floor(sec / 86400)}d ago`;
}

/* ── Hooks ───────────────────────────────────────────────────────────────── */

export function useHarnessRun(runId) {
  const [run, setRun] = useState(null);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    if (!runId) return;
    try {
      const res = await fetch(`${API_BASE}/api/harness-runs/${runId}`);
      if (!res.ok) throw new Error(`API ${res.status}`);
      const payload = await res.json();
      setRun(payload.run ?? payload);
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to load run');
    }
  }, [runId]);
  useEffect(() => {
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, [load]);
  return { run, error, reload: load };
}

export function useRunList() {
  const [runs, setRuns] = useState([]);
  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/harness-runs`);
      if (!res.ok) return;
      setRuns((await res.json()).runs || []);
    } catch {}
  }, []);
  useEffect(() => {
    load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, [load]);
  return { runs, reload: load };
}

export function useRunHistory(runId) {
  const [phaseTimeline, setPhaseTimeline] = useState([]);
  const [events, setEvents] = useState([]);
  const afterIdRef = React.useRef(0);

  const loadPhases = useCallback(async () => {
    if (!runId) return;
    try {
      const res = await fetch(`${API_BASE}/api/harness-runs/${runId}/phases`);
      if (!res.ok) return;
      setPhaseTimeline((await res.json()).phases || []);
    } catch {}
  }, [runId]);

  const loadEvents = useCallback(async () => {
    if (!runId) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/harness-runs/${runId}/events?after_id=${afterIdRef.current}&limit=100`,
      );
      if (!res.ok) return;
      const data = await res.json();
      if (data.events?.length) {
        afterIdRef.current = data.events[data.events.length - 1].id;
        setEvents((prev) => [...prev, ...data.events]);
      }
    } catch {}
  }, [runId]);

  useEffect(() => {
    setPhaseTimeline([]);
    setEvents([]);
    afterIdRef.current = 0;
    if (!runId) return;
    loadPhases();
    loadEvents();
    const pid = setInterval(loadPhases, 5000);
    const eid = setInterval(loadEvents, 3000);
    return () => { clearInterval(pid); clearInterval(eid); };
  }, [runId, loadPhases, loadEvents]);

  return { phaseTimeline, events };
}

export function useLogTail(runId) {
  const [lines, setLines] = useState([]);
  const load = useCallback(async () => {
    if (!runId) return;
    try {
      const res = await fetch(`${API_BASE}/api/harness-runs/${runId}/log?lines=300`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.available) setLines(data.lines || []);
    } catch {}
  }, [runId]);
  useEffect(() => {
    setLines([]);
    if (!runId) return;
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, [runId, load]);
  return lines;
}

export function useGateOutcomes(runId) {
  const [gates, setGates] = useState({});
  const load = useCallback(async () => {
    if (!runId) return;
    try {
      const res = await fetch(`${API_BASE}/api/harness-runs/${runId}/gates`);
      if (!res.ok) return;
      const data = await res.json();
      setGates(data.gates || data || {});
    } catch {}
  }, [runId]);
  useEffect(() => {
    setGates({});
    if (!runId) return;
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [runId, load]);
  return gates;
}

/* ── StatusPill ──────────────────────────────────────────────────────────── */

export function StatusPill({ status }) {
  return <span className={`statusPill ${status}`}>{statusLabel(status)}</span>;
}

/* ── Custom Phase Node (React Flow) ─────────────────────────────────────── */

const PhaseNodeInner = ({ data }) => {
  const { index, phaseName, phaseData, status, timelineEntry, isSelected } = data;
  const meta = PHASE_META[phaseName] || { label: phaseName, layer: 'SDLC', desc: '', Icon: FileText };
  const layer = LAYER_STYLE[meta.layer] || LAYER_STYLE.SDLC;

  const isRunning  = status === 'running';
  const isDone     = status === 'done';
  const isDoneFail = status === 'done-fail';
  const isFailed   = status === 'failed';

  let statusColor = '#5a5244';
  let StatusIcon  = <Circle size={13} />;
  if (isDone)                      { statusColor = '#8dcc61'; StatusIcon = <CheckCircle2 size={13} />; }
  else if (isDoneFail || isFailed) { statusColor = '#ffb39f'; StatusIcon = <AlertCircle size={13} />; }
  else if (isRunning)              { statusColor = '#65c6a5'; StatusIcon = <Activity size={13} className="spin" />; }

  const borderColor = isSelected
    ? layer.color
    : isRunning              ? layer.border
    : isDone                 ? 'rgba(58,96,48,0.9)'
    : isFailed || isDoneFail ? 'rgba(155,88,70,0.6)'
    : '#2e2b23';

  const bgColor = isSelected
    ? layer.bg
    : isRunning              ? 'rgba(101,198,165,0.06)'
    : isDone                 ? '#0e1c0a'
    : isFailed || isDoneFail ? '#160a09'
    : 'var(--c-surface-1)';

  const hasMetrics = phaseData && (
    phaseData.attempts > 0 ||
    timelineEntry?.duration_sec != null ||
    timelineEntry?.cost_usd > 0 ||
    phaseData.failed_gates?.length > 0
  );

  return (
    <div
      className={`pfn${isSelected ? ' pfn-selected' : ''}${isRunning ? ' pfn-pulsing' : ''}`}
      style={{ borderColor, background: bgColor, width: NODE_W, '--layer-color': layer.color }}
    >
      <Handle type="target" position={Position.Top} className="pfn-handle" />
      <div className="pfn-header">
        <span className="pfn-num">#{index}</span>
        <span className="pfn-layer-badge" style={{ color: layer.color, background: layer.bg, borderColor: layer.border }}>
          {meta.layer}
        </span>
        <span className="pfn-name">{meta.label}</span>
        <span className="pfn-status-icon" style={{ color: statusColor }}>{StatusIcon}</span>
      </div>
      <div className="pfn-desc">{meta.desc}</div>
      {hasMetrics && (
        <div className="pfn-metrics">
          {phaseData.attempts > 0 && <span>{phaseData.attempts}×</span>}
          {timelineEntry?.duration_sec != null && <span>{timelineEntry.duration_sec}s</span>}
          {timelineEntry?.cost_usd > 0 && <span>${Number(timelineEntry.cost_usd).toFixed(4)}</span>}
          {phaseData.failed_gates?.length > 0 && (
            <span className="pfn-metric-fail">{phaseData.failed_gates.length} gate{phaseData.failed_gates.length > 1 ? 's' : ''} failed</span>
          )}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="pfn-handle" />
    </div>
  );
};

export const PhaseNode = memo(PhaseNodeInner);
export const nodeTypes = { phaseNode: PhaseNode };

/* ── Build RF nodes & edges ──────────────────────────────────────────────── */

export function buildFlow(run, timelineMap, selectedPhase) {
  const phaseNames = run?.phases?.length
    ? run.phases.map((p) => p.name)
    : DEFAULT_PIPELINE;

  const phaseDataMap = {};
  if (run?.phases) for (const p of run.phases) phaseDataMap[p.name] = p;

  const nodes = phaseNames.map((name, i) => ({
    id: name,
    type: 'phaseNode',
    position: { x: 0, y: i * STEP },
    data: {
      index: i + 1,
      phaseName: name,
      phaseData: phaseDataMap[name] || null,
      status: phaseRunStatus(phaseDataMap[name], name, run?.current_phase, run?.status),
      timelineEntry: timelineMap[name] || null,
      isSelected: name === selectedPhase,
    },
  }));

  const edges = phaseNames.slice(0, -1).map((from, i) => {
    const to = phaseNames[i + 1];
    const fromDone = phaseDataMap[from]?.status === 'done';
    const edgeColor = fromDone ? '#3d7f69' : '#2a2721';
    return {
      id: `e-${from}-${to}`,
      source: from,
      target: to,
      type: 'smoothstep',
      animated: fromDone && run?.status === 'running',
      style: { stroke: edgeColor, strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor, width: 10, height: 10 },
    };
  });

  return { nodes, edges };
}

/* ── PipelineFlow canvas ─────────────────────────────────────────────────── */

export function PipelineFlow({ run, timelineMap, selectedPhase, onPhaseSelect }) {
  const initial = useMemo(() => buildFlow(run, timelineMap, selectedPhase), []);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);

  useEffect(() => {
    const { nodes: n, edges: e } = buildFlow(run, timelineMap, selectedPhase);
    setNodes(n);
    setEdges(e);
  }, [run, timelineMap, selectedPhase]);

  const handleNodeClick = useCallback(
    (_, node) => onPhaseSelect(node.id === selectedPhase ? null : node.id),
    [selectedPhase, onPhaseSelect],
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={handleNodeClick}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.14, minZoom: 0.25, maxZoom: 1.6 }}
      minZoom={0.2}
      maxZoom={2}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      colorMode="dark"
    >
      <Background color="#232018" gap={22} size={1} variant="dots" />
      <Controls showInteractive={false} position="bottom-left" />
      <MiniMap
        nodeColor={(n) => {
          const s = n.data?.status;
          if (s === 'done') return '#8dcc61';
          if (s === 'running') return '#65c6a5';
          if (s === 'failed' || s === 'done-fail') return '#ffb39f';
          return '#2e2b23';
        }}
        maskColor="rgba(0,0,0,0.65)"
        style={{ background: '#111111', border: '1px solid #2e2b23' }}
        position="bottom-right"
      />
      <Panel position="top-right">
        <div className="flowLegend">
          {Object.entries(LAYER_STYLE).map(([key, s]) => (
            <span key={key} className="legend-item">
              <span className="legend-dot" style={{ background: s.color }} />
              {key === 'SDLC' ? 'SDLC Phase' : `${key} Harness`}
            </span>
          ))}
          <span className="legend-divider" />
          <span className="legend-item"><span className="legend-dot" style={{ background: '#8dcc61' }} />Done</span>
          <span className="legend-item"><span className="legend-dot pulse-dot" style={{ background: '#65c6a5' }} />Running</span>
          <span className="legend-item"><span className="legend-dot" style={{ background: '#ffb39f' }} />Failed</span>
        </div>
      </Panel>
    </ReactFlow>
  );
}

/* ── ArtifactItem ────────────────────────────────────────────────────────── */

function ArtifactItem({ artifact, runId }) {
  const [expanded, setExpanded] = useState(false);
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);

  async function toggle() {
    if (expanded) { setExpanded(false); return; }
    if (content === null) {
      setLoading(true);
      try {
        const artifactId = artifact.path.replace('db://harness_artifacts/', '');
        const res = await fetch(`${API_BASE}/api/harness-runs/${runId}/artifacts/${artifactId}`);
        if (res.ok) setContent((await res.json()).content || '(empty)');
        else setContent('Failed to load content.');
      } catch {
        setContent('Error fetching content.');
      } finally {
        setLoading(false);
      }
    }
    setExpanded(true);
  }

  const sizeLabel = artifact.size > 0
    ? artifact.size >= 1024 ? `${(artifact.size / 1024).toFixed(1)} KB` : `${artifact.size} B`
    : null;

  return (
    <div className={`dp-artifact dp-artifact--btn${expanded ? ' dp-artifact--open' : ''}`}>
      <button className="dp-artifact-toggle" onClick={toggle} aria-expanded={expanded}>
        <FileText size={12} style={{ flexShrink: 0, marginTop: 1 }} />
        <div className="dp-artifact-meta">
          <span>{artifact.name}</span>
          <small>{artifact.artifact_type}{sizeLabel ? ` · ${sizeLabel}` : ''}</small>
        </div>
        {loading
          ? <Activity size={11} className="spin" style={{ flexShrink: 0 }} />
          : <ChevronDown size={11} className={`dp-artifact-chevron${expanded ? ' dp-artifact-chevron--open' : ''}`} />}
      </button>
      {expanded && (
        <pre className="dp-artifact-content">{content ?? 'Loading…'}</pre>
      )}
    </div>
  );
}

/* ── PhaseDetailPanel ────────────────────────────────────────────────────── */

export function PhaseDetailPanel({ run, selectedPhase, gatesByPhase, events, phaseTimeline, onClose }) {
  if (!selectedPhase) return null;

  const meta = PHASE_META[selectedPhase] || { label: selectedPhase, layer: 'SDLC', desc: '', Icon: FileText };
  const layer = LAYER_STYLE[meta.layer] || LAYER_STYLE.SDLC;
  const { Icon } = meta;
  const phaseData    = run?.phases?.find((p) => p.name === selectedPhase);
  const timelineEntry = phaseTimeline.find((t) => t.phase_name === selectedPhase);

  const phaseGates   = gatesByPhase[selectedPhase];
  const latestAttempt = phaseGates ? Math.max(...Object.keys(phaseGates).map(Number)) : null;
  const gateOutcomes  = latestAttempt != null ? (phaseGates[String(latestAttempt)] || phaseGates[latestAttempt] || []) : [];

  const phaseEvents  = events.filter((e) => e.phase === selectedPhase);
  const artifacts    = (run?.artifacts || []).filter((a) => {
    if (selectedPhase === 'H1-context') {
      return a.artifact_type === 'context_packet'
          || a.artifact_type === 'context_manifest'
          || a.name?.includes(selectedPhase);
    }
    return a.name?.includes(selectedPhase);
  });
  const runStatus    = phaseRunStatus(phaseData, selectedPhase, run?.current_phase, run?.status);

  return (
    <aside className="detailPanel">
      <div className="dp-header" style={{ borderBottomColor: layer.border }}>
        <div className="dp-title-row">
          <Icon size={14} style={{ color: layer.color, flexShrink: 0 }} />
          <span className="dp-layer-badge" style={{ color: layer.color, background: layer.bg, borderColor: layer.border }}>
            {meta.layer}
          </span>
          <span className="dp-title">{meta.label}</span>
          <button className="dp-close" onClick={onClose} title="Close" aria-label="Close panel">
            <X size={14} />
          </button>
        </div>
        <p className="dp-desc">{meta.desc}</p>
        <code className="dp-phase-id">{selectedPhase}</code>
      </div>

      <div className="dp-metrics">
        <div className="dp-metric">
          <span>Status</span>
          <strong className={`dp-status-val ${runStatus}`}>{statusLabel(phaseData?.status || 'pending')}</strong>
        </div>
        <div className="dp-metric">
          <span>Gate</span>
          <strong className={`dp-gate-val ${phaseData?.gate || ''}`}>{phaseData?.gate || '—'}</strong>
        </div>
        <div className="dp-metric">
          <span>Attempts</span>
          <strong>{phaseData?.attempts ?? '—'}</strong>
        </div>
        <div className="dp-metric">
          <span>Duration</span>
          <strong>{timelineEntry?.duration_sec != null ? `${timelineEntry.duration_sec}s` : '—'}</strong>
        </div>
        <div className="dp-metric">
          <span>Cost</span>
          <strong>{timelineEntry?.cost_usd > 0 ? `$${Number(timelineEntry.cost_usd).toFixed(4)}` : '—'}</strong>
        </div>
        <div className="dp-metric">
          <span>Agent</span>
          <strong className={timelineEntry?.agent_ok === true ? 'dp-status-val done' : timelineEntry?.agent_ok === false ? 'dp-status-val failed' : ''}>
            {timelineEntry?.agent_ok === true ? 'ok' : timelineEntry?.agent_ok === false ? 'error' : '—'}
          </strong>
        </div>
      </div>

      {gateOutcomes.length > 0 && (
        <div className="dp-section">
          <h4 className="dp-section-title">Gate Checks · attempt {latestAttempt}</h4>
          <div className="dp-gates">
            {gateOutcomes.map((g, i) => (
              <div key={i} className={`dp-gate ${g.passed ? 'pass' : 'fail'}`}>
                <span className="dp-gate-icon">
                  {g.passed ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
                </span>
                <div className="dp-gate-body">
                  <span className="dp-gate-name">{g.gate_name}</span>
                  <span className="dp-gate-type">{g.gate_type}</span>
                  {!g.passed && g.report && <p className="dp-gate-report">{g.report}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!gateOutcomes.length && phaseData?.failed_gates?.length > 0 && (
        <div className="dp-section">
          <h4 className="dp-section-title">Failed Gates</h4>
          <div className="dp-failed-tags">
            {phaseData.failed_gates.map((g) => <span key={g} className="gateTag">{g}</span>)}
          </div>
        </div>
      )}

      {phaseEvents.length > 0 && (
        <div className="dp-section">
          <h4 className="dp-section-title">Events</h4>
          <div className="dp-event-log">
            {phaseEvents.map((e) => (
              <div key={e.id} className={`eventRow ${e.event_type}`}>
                <span className="eventType">{EVENT_TYPE_LABELS[e.event_type] || e.event_type}</span>
                <span className="eventMsg">{e.message}</span>
                <span className="eventTime">{formatTime(e.occurred_at)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {artifacts.length > 0 && (
        <div className="dp-section">
          <h4 className="dp-section-title"><FileText size={12} />Artifacts <small style={{ fontWeight: 400, color: 'var(--c-on-surface-muted)' }}>— click to expand</small></h4>
          <div className="dp-artifacts">
            {artifacts.map((a) => (
              <ArtifactItem key={a.path} artifact={a} runId={run?.id} />
            ))}
          </div>
        </div>
      )}

      {!phaseData && !phaseEvents.length && !gateOutcomes.length && (
        <div className="dp-empty">
          <Circle size={22} />
          <span>Phase not started yet.</span>
          <small>Executes when the harness reaches this step.</small>
        </div>
      )}
    </aside>
  );
}

/* ── RunOutputPanel ──────────────────────────────────────────────────────── */

/* ── AppNav ──────────────────────────────────────────────────────────────── */

export function AppNav() {
  return (
    <nav className="appNav" aria-label="Main navigation">
      <div className="appNav-brand">
        <span className="appNav-brand-name">AI SDLC Harness</span>
        <span className="appNav-brand-tag">H1 · H3 · H4 · H7</span>
      </div>
      <div className="appNav-links">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `appNav-link${isActive ? ' appNav-link--active' : ''}`}
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/execute"
          className={({ isActive }) => `appNav-link${isActive ? ' appNav-link--active' : ''}`}
        >
          New Run
        </NavLink>
      </div>
    </nav>
  );
}

export function RunOutputPanel({ run, events }) {
  const [tab, setTab] = useState('events');
  const eventsEndRef = React.useRef(null);
  const logEndRef    = React.useRef(null);
  const logLines     = useLogTail(run?.id);

  useEffect(() => {
    if (tab === 'events') eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length, tab]);

  useEffect(() => {
    if (tab === 'log') logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logLines.length, tab]);

  const failedPhases = (run?.phases || []).filter((p) => p.status === 'failed');

  return (
    <aside className="detailPanel">
      <div className="dp-header">
        <div className="dp-title-row">
          <span className="dp-title">Run Output</span>
          <StatusPill status={run?.status || 'idle'} />
        </div>
        {run?.id && <code className="dp-phase-id">{run.id}</code>}
      </div>

      {run && ['escalated', 'failed', 'stopped'].includes(run.status) && (
        <div className={`escalationBanner ${run.status}`}>
          <AlertCircle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
          <div>
            <strong>Run {statusLabel(run.status)}</strong>
            {failedPhases.length > 0 && <span> — failed at: {failedPhases.map((p) => p.name).join(', ')}</span>}
          </div>
        </div>
      )}

      <div className="dp-metrics">
        <div className="dp-metric"><span>Target</span><strong>{run?.target || '—'}</strong></div>
        <div className="dp-metric"><span>Mode</span><strong>{run?.mode || '—'}</strong></div>
        <div className="dp-metric"><span>Provider</span><strong>{run?.provider || '—'}</strong></div>
        <div className="dp-metric"><span>Total Cost</span><strong>${Number(run?.cost_usd || 0).toFixed(4)}</strong></div>
        <div className="dp-metric"><span>Return</span><strong>{run?.return_code ?? '—'}</strong></div>
        <div className="dp-metric">
          <span>Phases</span>
          <strong>
            {run?.phases ? `${run.phases.filter((p) => p.status === 'done').length} / ${run.phases.length}` : '—'}
          </strong>
        </div>
      </div>

      {run?.artifacts?.length > 0 && (
        <div className="dp-section">
          <h4 className="dp-section-title"><FileText size={12} />Artifacts <small style={{ fontWeight: 400, color: 'var(--c-on-surface-muted)' }}>— click to expand</small></h4>
          <div className="dp-artifacts">
            {run.artifacts.map((a) => (
              <ArtifactItem key={a.path} artifact={a} runId={run?.id} />
            ))}
          </div>
        </div>
      )}

      {/* ── Log tab switcher ── */}
      <div className="dp-section dp-section-grow">
        <div className="dp-tabs">
          <button
            className={`dp-tab${tab === 'events' ? ' dp-tab--active' : ''}`}
            onClick={() => setTab('events')}
          >
            <Terminal size={11} />
            Events
            {events.length > 0 && <span className="dp-tab-badge">{events.length}</span>}
          </button>
          <button
            className={`dp-tab${tab === 'log' ? ' dp-tab--active' : ''}`}
            onClick={() => setTab('log')}
          >
            <Code2 size={11} />
            System Log
            {logLines.length > 0 && <span className="dp-tab-badge">{logLines.length}</span>}
          </button>
        </div>

        {tab === 'events' && (
          <div className="dp-event-log dp-event-log-fill">
            {events.length === 0 ? (
              <div className="dp-empty-log">
                {run?.log_tail?.length ? run.log_tail.join('\n') : 'Waiting for harness events…'}
              </div>
            ) : (
              events.map((e) => (
                <div key={e.id} className={`eventRow ${e.event_type}`}>
                  <span className="eventType">{EVENT_TYPE_LABELS[e.event_type] || e.event_type}</span>
                  <span className="eventPhase">{e.phase || ''}</span>
                  <span className="eventMsg">{e.message}</span>
                  <span className="eventTime">{formatTime(e.occurred_at)}</span>
                </div>
              ))
            )}
            <div ref={eventsEndRef} />
          </div>
        )}

        {tab === 'log' && (
          <div className="dp-event-log dp-event-log-fill dp-raw-log">
            {logLines.length === 0 ? (
              <div className="dp-empty-log">No system log yet — log file written when run starts.</div>
            ) : (
              logLines.map((line, i) => (
                <div key={i} className="rawLogLine">{line || ' '}</div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        )}
      </div>
    </aside>
  );
}
