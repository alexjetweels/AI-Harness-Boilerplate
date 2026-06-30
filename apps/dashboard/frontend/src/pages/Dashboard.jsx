import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, CircleAlert } from 'lucide-react';
import {
  AppNav,
  relativeTime,
  useRunList,
  StatusPill,
} from '../shared';

/* ── Stats strip ─────────────────────────────────────────────────────────── */

function StatsStrip({ runs }) {
  const total   = runs.length;
  const running = runs.filter((r) => r.status === 'running' || r.status === 'queued').length;
  const done    = runs.filter((r) => r.status === 'complete').length;
  const failed  = runs.filter((r) => ['failed', 'escalated'].includes(r.status)).length;
  const totalCost = runs.reduce((s, r) => s + (Number(r.cost_usd) || 0), 0);

  return (
    <div className="statsStrip">
      <StatCard label="Total Runs"   value={total}                       />
      <StatCard label="Running"      value={running} accent="primary"    />
      <StatCard label="Complete"     value={done}    accent="success"    />
      <StatCard label="Failed"       value={failed}  accent="error"      />
      <StatCard label="Total Cost"   value={`$${totalCost.toFixed(3)}`}  />
    </div>
  );
}

function StatCard({ label, value, accent }) {
  const cls = accent ? `statCard statCard--${accent}` : 'statCard';
  return (
    <div className={cls}>
      <span className="statCard-label">{label}</span>
      <strong className="statCard-value">{value}</strong>
    </div>
  );
}

/* ── Runs table ──────────────────────────────────────────────────────────── */

function phaseSummary(phases) {
  if (!phases?.length) return '—';
  const done = phases.filter((p) => p.status === 'done').length;
  return `${done} / ${phases.length}`;
}

function RunsTable({ runs, onView }) {
  if (!runs.length) {
    return (
      <div className="runsEmpty">
        <CircleAlert size={20} />
        <span>No runs yet. Start a new run above to get going.</span>
      </div>
    );
  }

  return (
    <div className="runsTableWrap">
      <table className="runsTable">
        <thead>
          <tr>
            <th>#</th>
            <th>Run ID</th>
            <th>Status</th>
            <th>Feature</th>
            <th>Target</th>
            <th>Mode</th>
            <th>Phases</th>
            <th>Cost</th>
            <th>Started</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {runs.map((run, i) => (
            <RunRow key={run.id} run={run} index={i + 1} onView={onView} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RunRow({ run, index, onView }) {
  const isRunning = run.status === 'running' || run.status === 'queued';
  const isFailed  = ['failed', 'escalated'].includes(run.status);

  return (
    <tr
      className={`runsRow${isRunning ? ' runsRow--running' : ''}${isFailed ? ' runsRow--failed' : ''}`}
      onClick={() => onView(run.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onView(run.id)}
    >
      <td className="col-index">{index}</td>
      <td className="col-id"><code>{run.id?.slice(0, 18) || '—'}</code></td>
      <td className="col-status"><StatusPill status={run.status} /></td>
      <td className="col-feature" title={run.feature}>{run.feature?.slice(0, 52) || '—'}</td>
      <td className="col-target">{run.target || '—'}</td>
      <td className="col-mode">{run.mode || '—'}</td>
      <td className="col-phases">{phaseSummary(run.phases)}</td>
      <td className="col-cost">${Number(run.cost_usd || 0).toFixed(3)}</td>
      <td className="col-started">{relativeTime(run.created_at)}</td>
      <td className="col-action">
        <button className="viewPipelineBtn" onClick={(e) => { e.stopPropagation(); onView(run.id); }}>
          Pipeline <ArrowRight size={12} />
        </button>
      </td>
    </tr>
  );
}

/* ── Dashboard page ──────────────────────────────────────────────────────── */

export default function Dashboard() {
  const navigate = useNavigate();
  const { runs } = useRunList();

  return (
    <div className="dashPage">
      <AppNav />
      <div className="dashContent">
        <StatsStrip runs={runs} />

        <div className="runsSectionHeader">
          <h2>Recent Runs</h2>
          <span className="runsSectionCount">{runs.length} total</span>
        </div>

        <RunsTable runs={runs} onView={(id) => navigate(`/pipeline/${id}`)} />
      </div>
    </div>
  );
}
