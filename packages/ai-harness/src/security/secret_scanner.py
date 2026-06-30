"""Secret scanning primitives used by H3 gates and future H4 policies."""
import glob
import os
import re

from agentops import storage


DEFAULT_SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
    r"-----BEGIN (RSA|OPENSSH|EC|DSA)? ?PRIVATE KEY-----",
]

DEFAULT_EXCLUDE = [".git/**", "node_modules/**", ".venv/**", "venv/**"]


def _expand(s: str, ctx: dict) -> str:
    for k, v in ctx.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def _db_artifact_id(ref: str) -> str:
    prefix = "db://harness_artifacts/"
    return ref[len(prefix):] if ref.startswith(prefix) else ""


def _scan_text(name: str, text: str, compiled: list[re.Pattern]) -> list[str]:
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for rx in compiled:
            if "[:=]" in rx.pattern and ":" not in line and "=" not in line:
                continue
            if rx.search(line):
                hits.append(f"{name}:{i}: {rx.pattern}")
    return hits


def scan_for_secrets(repo: str, ctx: dict, params: dict) -> list[str]:
    patterns = params.get("patterns") or DEFAULT_SECRET_PATTERNS
    include = params.get("include", ["**/*"])
    exclude = params.get("exclude", DEFAULT_EXCLUDE)
    compiled = [re.compile(item) for item in patterns]

    excluded = []
    for pat in exclude:
        excluded.extend(glob.glob(os.path.join(repo, _expand(pat, ctx)), recursive=True))
    excluded_abs = {os.path.abspath(item) for item in excluded}

    hits = []
    for pat in include:
        expanded = _expand(pat, ctx)
        artifact_id = _db_artifact_id(expanded)
        if artifact_id:
            hits.extend(_scan_text(expanded, storage.artifact_content(artifact_id), compiled))
            continue

        for path in glob.glob(os.path.join(repo, expanded), recursive=True):
            path_abs = os.path.abspath(path)
            if os.path.isdir(path) or path_abs in excluded_abs:
                continue
            if any(path_abs.startswith(excluded_path + os.sep)
                   for excluded_path in excluded_abs
                   if os.path.isdir(excluded_path)):
                continue
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    hits.extend(_scan_text(os.path.relpath(path, repo), fh.read(), compiled))
            except OSError:
                pass
    return hits
