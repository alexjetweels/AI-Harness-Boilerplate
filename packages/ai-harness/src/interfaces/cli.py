"""`harness` CLI: run, resume, status."""
import argparse
import asyncio
import json
import os
import re
import sys
import time

from agentops import state_store
from core import config as config_mod
from orchestration import code_chat
from orchestration import orchestrator


def _slug(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]
    return f"{base}-{time.strftime('%Y%m%d-%H%M%S')}"


def _config_path(repo: str, config: str) -> str:
    """Resolve package-owned configs without requiring target repo changes."""
    if os.path.isabs(config) or os.path.exists(config):
        return config
    return os.path.join(repo, config)


# Cheapest model per provider — a model id from one provider is invalid on
# the other (e.g. Codex's "gpt-5.4-mini" 404s against the Claude API), so
# switching provider must carry the model along with it.
_CHEAP_MODEL = {"claude": "haiku", "codex": "gpt-5.4-mini"}


def _override_provider(cfg, provider: str | None) -> None:
    if not provider:
        return
    if provider != cfg.agent.provider:
        cfg.agent.model = _CHEAP_MODEL.get(provider, cfg.agent.model)
    cfg.agent.provider = provider
    if getattr(cfg.agent, "bin", "") in {"", "claude", "codex"}:
        cfg.agent.bin = provider


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="harness", description="Spec-Kit SDLC harness for Claude Code")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="Run the full pipeline for a feature")
    pr.add_argument("--feature", required=True)
    pr.add_argument("--config", default="harness.yaml")
    pr.add_argument("--repo", default=".")
    pr.add_argument("--run-id", default=None)
    pr.add_argument("--provider", choices=["claude", "codex"], default=None)
    pr.add_argument("--tech-stack", default="", help="passed to /speckit.plan")
    pr.add_argument("--constitution", default="Code quality, testing standards, UX consistency, performance")

    rs = sub.add_parser("resume", help="Resume an existing run")
    rs.add_argument("run_id")
    rs.add_argument("--config", default="harness.yaml")
    rs.add_argument("--repo", default=".")
    rs.add_argument("--provider", choices=["claude", "codex"], default=None)

    st = sub.add_parser("status", help="Show run status")
    st.add_argument("run_id")
    st.add_argument("--config", default="harness.yaml")
    st.add_argument("--repo", default=".")

    cc = sub.add_parser("code-chat", help="Run Copilot-style code chat workflow from JSON stdin")
    cc.add_argument("--repo", default=".")
    cc.add_argument("--stream", action="store_true", help="Emit session snapshots as JSONL")

    args = p.parse_args(argv)

    if args.cmd == "code-chat":
        try:
            payload = json.loads(sys.stdin.read() or "{}")
            if args.stream:
                def emit(snapshot: dict) -> None:
                    print(json.dumps(snapshot, ensure_ascii=False), flush=True)
                result = asyncio.run(code_chat.run(payload, repo=args.repo, emit=emit))
            else:
                result = code_chat.run_sync(payload, repo=args.repo)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result.get("status") not in {"failed"} else 1
        except Exception as exc:
            print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
            return 1

    cfg = config_mod.load(_config_path(args.repo, args.config))

    if args.cmd == "run":
        _override_provider(cfg, args.provider)
        run_id = args.run_id or _slug(args.feature)
        ctx_extra = {"tech_stack": args.tech_stack, "constitution": args.constitution}
        return orchestrator.run(cfg, args.feature, run_id, repo=args.repo, ctx_extra=ctx_extra)

    if args.cmd == "resume":
        _override_provider(cfg, args.provider)
        s = state_store.load(os.path.join(args.repo, cfg.state_dir), args.run_id)
        return orchestrator.run(cfg, s["feature"], args.run_id, repo=args.repo, resume=True)

    if args.cmd == "status":
        s = state_store.load(os.path.join(args.repo, cfg.state_dir), args.run_id)
        print(f"Run {s['run_id']}  status={s['status']}  cost=${s['cost_usd']}  feature_dir={s.get('feature_dir')}")
        for name, ph in s["phases"].items():
            print(f"  {name:14} {str(ph.get('status')):8} gate={ph.get('gate')} attempts={ph.get('attempts')}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
