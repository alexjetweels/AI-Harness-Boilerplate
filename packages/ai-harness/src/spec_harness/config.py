"""Load and validate harness.yaml."""
from dataclasses import dataclass, field
import yaml


@dataclass
class Gate:
    name: str
    type: str               # shell | glob_nonempty | no_markers | agent_output
    params: dict


@dataclass
class Phase:
    name: str
    command: str | None      # slash command template, e.g. "/speckit.specify {feature}". None = gate-only phase.
    max_attempts: int
    gates: list
    skip_if_exists: str | None = None


@dataclass
class AgentConfig:
    provider: str = "claude"               # claude | codex
    bin: str = "claude"
    model: str = "sonnet"
    max_turns: int = 40
    max_budget_usd: float = 0.0          # 0 = no per-call cap
    allowed_tools: str = "Read,Write,Edit,Bash"
    skip_permissions: bool = True        # unattended runs; ONLY inside a sandbox
    extra_args: list = field(default_factory=list)


@dataclass
class HarnessConfig:
    agent: AgentConfig
    phases: list
    project: dict
    specs_glob: str
    state_dir: str
    runs_dir: str


def _expand_project(value, project):
    """Replace ${project.key} placeholders anywhere in strings/dicts/lists."""
    if isinstance(value, str):
        for k, v in project.items():
            value = value.replace("${project." + k + "}", str(v))
        return value
    if isinstance(value, dict):
        return {k: _expand_project(v, project) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_project(v, project) for v in value]
    return value


def load(path: str) -> HarnessConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    project = raw.get("project", {})
    agent = AgentConfig(**raw.get("agent", {}))

    phases = []
    for p in raw["phases"]:
        gates = [
            Gate(g["name"], g["type"], _expand_project(g.get("params", {}), project))
            for g in p.get("gates", [])
        ]
        phases.append(Phase(
            name=p["name"],
            command=p.get("command"),
            max_attempts=p.get("max_attempts", 1),
            gates=gates,
            skip_if_exists=p.get("skip_if_exists"),
        ))

    return HarnessConfig(
        agent=agent,
        phases=phases,
        project=project,
        specs_glob=raw.get("specs_glob", "specs/*"),
        state_dir=raw.get("state_dir", ".specify/state"),
        runs_dir=raw.get("runs_dir", ".specify/runs"),
    )
