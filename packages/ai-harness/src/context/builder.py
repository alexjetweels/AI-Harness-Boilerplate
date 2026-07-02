"""Build the H1 context packet for a harness run."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from agentops import storage


@dataclass
class ContextSource:
    path: str
    role: str
    required: bool
    size: int
    sha256: str


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _read_text(path: Path, max_bytes: int) -> tuple[str, int, str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw[:max_bytes].decode("utf-8", errors="ignore")
    if len(raw) > max_bytes:
        text += f"\n\n[TRUNCATED: original file has {len(raw)} bytes, limit is {max_bytes} bytes]\n"
    return text, len(raw), digest


def _matches(repo: Path, pattern: str) -> list[Path]:
    found = glob.glob(str(repo / pattern), recursive=True)
    return [Path(item) for item in sorted(found) if Path(item).is_file()]


def build(repo: str, run_id: str, feature: str, cfg: dict, phase_names: list[str] | None = None) -> dict:
    """Create a bounded Markdown context packet and JSON manifest.

    The packet is intentionally file-based so every provider sees the same
    target context regardless of whether slash commands are native or inlined.

    Each source may carry a `phases: [...]` list scoping it to specific phase
    names. Sources without `phases` (or with an empty list) are global and
    included everywhere. In addition to the full packet (used for the H1
    manifest/audit trail), this builds one filtered packet per name in
    `phase_names` containing only the sources relevant to that phase — so a
    phase like `srs` doesn't pay to load `docs/technical_architecture.md` or
    implementation-only protocol files it never needs.
    """
    if not cfg:
        return {}

    repo_path = Path(repo)
    max_file_bytes = int(cfg.get("max_file_bytes", 50000))
    max_total_bytes = int(cfg.get("max_total_bytes", 250000))
    total = 0
    # Each entry: (phases_filter: list[str] | None, section_text: str)
    sections: list[tuple[list[str] | None, str]] = []
    manifest_sources: list[ContextSource] = []
    missing_required = []

    for source in _as_list(cfg.get("sources")):
        pattern = source.get("path", "")
        role = source.get("role", "context")
        required = bool(source.get("required", False))
        phases_filter = source.get("phases") or None
        paths = _matches(repo_path, pattern)
        if required and not paths:
            missing_required.append(pattern)
        for path in paths:
            if total >= max_total_bytes:
                break
            rel = path.relative_to(repo_path).as_posix()
            remaining = max_total_bytes - total
            text, size, digest = _read_text(path, min(max_file_bytes, remaining))
            total += len(text.encode("utf-8", errors="ignore"))
            manifest_sources.append(ContextSource(rel, role, required, size, digest))
            sections.append((
                phases_filter,
                f"## {role}: `{rel}`\n\n"
                f"```text\n{text}\n```\n",
            ))

    def _header(scope: str, count: int) -> str:
        text = (
            "# Harness Context Packet\n\n"
            f"- run_id: `{run_id}`\n"
            f"- feature: {feature}\n"
            f"- scope: {scope}\n"
            f"- generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
            f"- source_count: {count}\n\n"
        )
        if missing_required:
            text += "## Missing Required Sources\n\n" + "\n".join(f"- `{item}`" for item in missing_required) + "\n\n"
        return text

    def _render(phase_name: str | None) -> tuple[str, int]:
        parts = [
            text for (phases_filter, text) in sections
            if phase_name is None or not phases_filter or phase_name in phases_filter
        ]
        scope = f"phase={phase_name}" if phase_name else "full run (all sources)"
        return _header(scope, len(parts)) + "\n".join(parts), len(parts)

    packet_content, _ = _render(None)
    manifest_json = json.dumps({
        "run_id": run_id,
        "feature": feature,
        "missing_required": missing_required,
        "source_count": len(manifest_sources),
        "sources": [item.__dict__ for item in manifest_sources],
    }, indent=2)

    packet_id = storage.save_artifact(
        run_id,
        "context_packet",
        f"{run_id}.context.md",
        content=packet_content,
        payload={"source_count": len(manifest_sources)},
    )
    manifest_id = storage.save_artifact(
        run_id,
        "context_manifest",
        f"{run_id}.manifest.json",
        content=manifest_json,
        payload=json.loads(manifest_json),
    )

    # Also persist to real files under the run repo so agents can read the
    # packet directly with their Read tool. The `db://...` id is only used
    # for the H1 "artifact exists" gate — it is not a filesystem path, so
    # without this the orchestrator has no choice but to re-paste the full
    # packet text into every single phase prompt (see orchestrator._inject_context).
    packet_rel = manifest_rel = None
    phase_packets_rel: dict[str, str] = {}
    packet_dir = str(cfg.get("packet_dir") or "").strip()
    if packet_dir:
        try:
            out_dir = repo_path / packet_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            packet_path = out_dir / f"{run_id}.context.md"
            manifest_path = out_dir / f"{run_id}.manifest.json"
            packet_path.write_text(packet_content, encoding="utf-8")
            manifest_path.write_text(manifest_json, encoding="utf-8")
            packet_rel = packet_path.relative_to(repo_path).as_posix()
            manifest_rel = manifest_path.relative_to(repo_path).as_posix()

            # One filtered packet per phase — a phase whose sources are all
            # global ends up identical in content to the full packet, but
            # still gets its own small file so _inject_context always has a
            # single, unambiguous path to point at for that phase.
            for phase_name in phase_names or []:
                phase_content, included = _render(phase_name)
                if included == 0:
                    continue  # gate-only phase with no command never reads a packet
                phase_path = out_dir / f"{run_id}.{phase_name}.context.md"
                phase_path.write_text(phase_content, encoding="utf-8")
                phase_packets_rel[phase_name] = phase_path.relative_to(repo_path).as_posix()
        except OSError:
            packet_rel = manifest_rel = None
            phase_packets_rel = {}

    return {
        "context_packet": packet_rel or f"db://harness_artifacts/{packet_id}",
        "context_manifest": manifest_rel or f"db://harness_artifacts/{manifest_id}",
        "context_packet_id": packet_id,
        "context_manifest_id": manifest_id,
        "context_packet_content": packet_content,
        "context_missing_required": ",".join(missing_required),
        "phase_context_packets": phase_packets_rel,
    }
