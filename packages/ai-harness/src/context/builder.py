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


def build(repo: str, run_id: str, feature: str, cfg: dict) -> dict:
    """Create a bounded Markdown context packet and JSON manifest.

    The packet is intentionally file-based so every provider sees the same
    target context regardless of whether slash commands are native or inlined.
    """
    if not cfg:
        return {}

    repo_path = Path(repo)
    max_file_bytes = int(cfg.get("max_file_bytes", 50000))
    max_total_bytes = int(cfg.get("max_total_bytes", 250000))
    total = 0
    sections = []
    manifest_sources: list[ContextSource] = []
    missing_required = []

    for source in _as_list(cfg.get("sources")):
        pattern = source.get("path", "")
        role = source.get("role", "context")
        required = bool(source.get("required", False))
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
            sections.append(
                f"## {role}: `{rel}`\n\n"
                f"```text\n{text}\n```\n"
            )

    header = (
        "# Harness Context Packet\n\n"
        f"- run_id: `{run_id}`\n"
        f"- feature: {feature}\n"
        f"- generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"- source_count: {len(manifest_sources)}\n\n"
    )
    if missing_required:
        header += "## Missing Required Sources\n\n" + "\n".join(f"- `{item}`" for item in missing_required) + "\n\n"

    packet_content = header + "\n".join(sections)

    manifest = {
        "run_id": run_id,
        "feature": feature,
        "missing_required": missing_required,
        "source_count": len(manifest_sources),
        "sources": [item.__dict__ for item in manifest_sources],
    }
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
        content=json.dumps(manifest, indent=2),
        payload=manifest,
    )

    return {
        "context_packet": f"db://harness_artifacts/{packet_id}",
        "context_manifest": f"db://harness_artifacts/{manifest_id}",
        "context_packet_id": packet_id,
        "context_manifest_id": manifest_id,
        "context_packet_content": packet_content,
        "context_missing_required": ",".join(missing_required),
    }
