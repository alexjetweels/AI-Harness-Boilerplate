# AI SDLC Harness — Tài Liệu Requirement Hợp Nhất

**Version:** 2.0  
**Ngày cập nhật:** 2026-06-30  
**Trạng thái:** Tài liệu chính thống — dùng xuyên suốt toàn bộ dự án

---

## 1. Mục Tiêu Dự Án

Xây dựng một **AI SDLC Harness** — lớp control plane bên ngoài có khả năng bọc bất kỳ AI agent/prompt pack nào, điều phối toàn bộ vòng đời SDLC (requirement → design → code → test → review → release) một cách tự động, có kiểm soát, có thể audit và có thể tái sử dụng với nhiều dự án khác nhau.

### Mục tiêu cụ thể

```
1. Harness đủ thông minh để tự động điều phối prompt templates chạy tuần tự qua
   các phase SDLC mà không cần can thiệp thủ công.

2. Kết quả cuối cùng có thể kiểm chứng được: sinh ra frontend + backend code
   (dùng AINative_OKR_Claude_GHCP/ làm target đầu tiên).

3. Harness là provider-agnostic: chỉ cần đổi config YAML là nối được với
   Claude Code, Codex CLI, Copilot hoặc agent khác.

4. Harness là target-agnostic: đặt một file harness.<target>.yaml là bọc được
   dự án mới bất kỳ mà không sửa harness engine.
```

### Nguyên tắc thiết kế

> **Worker agents execute. Harness controls, evaluates, governs and observes.**

Harness không viết lại prompt pack hay agent logic của target. Nó bọc bên ngoài, đưa context vào, gọi agent, chạy gate, escalate khi fail, lưu mọi thứ vào Postgres.

---

## 2. Phạm Vi

### In Scope

- Engine harness chung 7 layer (H1–H7) bằng Python
- Provider adapter cho Claude Code CLI và Codex CLI (hiện có)
- Provider adapter mở rộng cho Copilot và internal agent (tương lai)
- Target adapter pattern: 1 YAML file per target project
- Deterministic gate system (shell, glob, marker, secret scan, DB artifact)
- H1 context packet builder: tập hợp có kiểm soát ngữ cảnh cho agent
- Postgres persistence: run state, phase events, gate outcomes, artifacts, logs
- Dashboard FastAPI + React để khởi động, quan sát và debug run
- End-to-end test target: `AINative_OKR_Claude_GHCP/` — OKR web app với
  13-step SDLC pipeline, sinh ra FE + BE code

### Out of Scope (MVP)

- Agent tự merge vào main không cần người duyệt
- Agent tự deploy production
- Agent tự chạy database migration trên production
- Thay thế hoàn toàn Jira, GitHub, CI/CD hiện có
- RAG/vector store đầy đủ (H1 hiện dùng file-based context packet)
- OPA/Rego policy engine đầy đủ (H2 hiện enforce qua allowed_tools config)
- Multi-tenant isolation

---

## 3. Kiến Trúc Tổng Thể

### Pattern: Outer Control Plane / Inner Agent System

```
User / Dashboard / CLI
         │
         ▼
  packages/ai-harness          ← Harness Engine (Python)
  ├── H1 Context Builder       ← tập hợp context có kiểm soát
  ├── H2 Tool/Agent Runner     ← provider adapter layer
  ├── H3 Evaluation Gates      ← deterministic pass/fail
  ├── H4 Security Scanner      ← secret scan, injection check
  ├── H5 Governance/Escalation ← retry, escalate, approval
  ├── H6 AgentOps/Storage      ← Postgres state/artifacts/logs
  └── H7 Orchestrator          ← phase loop, resume, repair
         │
         ▼ (đọc adapter YAML)
  packages/ai-harness/targets/okr-ghcp/harness.okr.yaml
         │
         ▼ (gọi inner system)
  AINative_OKR_Claude_GHCP/    ← Target OKR (prompt pack, agents, Spec-Kit)
  ├── .claude/commands/        ← slash commands
  ├── .claude/agents/          ← inner specialist agents
  ├── .specify/                ← Spec-Kit memory, scripts, templates
  └── docs/input/              ← business requirements, change requests
         │
         ▼
  Generated SDLC Artifacts     ← SRS, design, spec, plan, code, tests
  ├── backend/ (NestJS )
  └── frontend/ (React)
         │
         ▼
  PostgreSQL                   ← run_id, phase_events, gate_outcomes, artifacts
         │
         ▼
  Dashboard (FastAPI + React)  ← observe, debug, re-run
```

### Hai Mode Orchestration

| Mode | Config | Khi nào dùng |
|---|---|---|
| **Expanded** | `harness.okr.yaml` | Production visibility, phase-level retry, quan sát từng bước |
| **Boss** | `harness.okr.boss.yaml` | Tương thích nhanh với `/okr.bossbuiltin`, ít chi tiết hơn |

---

## 4. Tech Stack

### 4.1 Harness Engine (`packages/ai-harness/`)

| Thành phần | Lựa chọn | Lý do |
|---|---|---|
| Language | **Python 3.11+** | Team chuẩn, hợp subprocess/agent SDK |
| Config | **PyYAML** | YAML adapter file, đơn giản, không phụ thuộc |
| Postgres client | **psycopg2** | Trực tiếp, không ORM, dễ kiểm soát schema |
| Data validation | **dataclasses** (hiện tại) → **Pydantic v2** (khi cần) | Migrate khi có API layer |
| CLI | **argparse** (hiện tại) → **Typer** (khi expand) | Đủ cho MVP |
| Secret scan | **regex pattern match** (hiện tại) → **detect-secrets / Gitleaks** | Upgrade H4 |
| Testing | **pytest + pytest-asyncio** | Standard |
| Packaging | **pyproject.toml** (uv/pip) | Modern packaging |

### 4.2 Dashboard Backend (`apps/dashboard/backend/`)

| Thành phần | Lựa chọn |
|---|---|
| Framework | **FastAPI** |
| Async | **asyncio + asyncpg** (hoặc psycopg2 trong threadpool) |
| Schema | **Pydantic v2** |
| Process spawn | **subprocess** (spawn `python -m cli run`) |

### 4.3 Dashboard Frontend (`apps/dashboard/frontend/`)

| Thành phần | Lựa chọn |
|---|---|
| Framework | **React 18 + Vite** |
| State | fetch + polling (đơn giản, đủ MVP) |
| Styling | **Tailwind CSS** hoặc CSS modules |

### 4.4 Infrastructure

| Thành phần | Lựa chọn |
|---|---|
| Database | **PostgreSQL 15+** (Docker Compose) |
| Container | **Docker + docker-compose.yml** |
| Env | `.env` với `HARNESS_DB_URL` hoặc `DATABASE_URL` |

### 4.5 Provider CLI (ngoài harness, phải cài sẵn)

| Provider | Binary | Ghi chú |
|---|---|---|
| Claude Code | `claude` | `claude -p --output-format json` |
| Codex CLI | `codex` | `codex exec --json` |
| Copilot (tương lai) | TBD | Sẽ thêm adapter |

---

## 5. Cấu Trúc Thư Mục Chuẩn

```
AI-Harness-Boilerplate/
  apps/
    dashboard/
      backend/
        app/
          main.py          # FastAPI endpoints
          db.py            # Postgres connect + schema bootstrap
          db_logger.py     # Query helpers cho dashboard
      frontend/
        src/
          main.jsx         # React UI
          styles.css

  packages/
    ai-harness/
      pyproject.toml
      README.md
      harness.yaml         # Generic SDLC harness config (template)
      harness.sdlc.yaml    # Project-level defaults
      targets/
        okr-ghcp/
          harness.okr.yaml          # Expanded mode adapter
          harness.okr.boss.yaml     # Boss mode adapter
          commands/                 # Fallback command wrappers
            okr.bd.md
            okr.dd.md
            okr.reviewplan.md
            okr.testkit.md
      src/
        __main__.py
        cli.py
        interfaces/
          cli.py            # Typer/argparse entrypoint: run, resume, status
        core/
          config.py         # Load + validate harness YAML → HarnessConfig
        context/
          builder.py        # H1: context packet + manifest → Postgres
        tool/
          agent_runner.py   # H2: Claude/Codex adapter, slash command inline
        evaluation/
          gates.py          # H3: shell, glob, no_markers, secret_scan, db_artifact
        security/
          secret_scanner.py # H4: pattern-based secret detection
        governance/
          escalation.py     # H5: retry/escalate/approval boundary
        agentops/
          storage.py        # H6: Postgres schema + artifact persistence
          state_store.py    # H6: run state facade (file + DB sync)
          db_logger.py      # H6: phase/gate/event logger
        orchestration/
          orchestrator.py   # H7: phase loop, retry, resume, feedback inject

  harness/                  # Blueprint tái sử dụng (không phải code chạy)
    README.md
    layers/
      H1-context/policy.md
      H2-tool/policy.md
      H3-evaluation/policy.md
      H4-security/policy.md
      H5-governance/policy.md
      H6-agentops/policy.md
      H7-orchestration/policy.md
    targets/
      okr-ghcp/target.yaml

  AINative_OKR_Claude_GHCP/  # Target đầu tiên: OKR prompt pack (không sửa)
    CLAUDE.md
    README.md
    .claude/
      commands/
      agents/
        protocols/
        steps/
        templates/
    .specify/
    docs/
      input/
        okr-requirement.md
      technical_architecture.md

  docs/
    REQUIREMENTS.md          ← file này
    architecture.md
    ai-sdlc-harness-flow-understanding.md
    ai-sdlc-harness-wrapper-architecture.md
    okr-harness-7-level-report.md

  docker-compose.yml
  .env.example
```

---

## 6. 7 Layer Harness (H1–H7)

### H1 — Context Harness

**Mục tiêu:** Đưa đúng thông tin, đúng lúc, đúng quyền vào agent. Không để agent đọc file ngoài phạm vi, không dùng tài liệu cũ.

**Cách hoạt động hiện tại:**
- Đọc các file nguồn được khai báo trong adapter YAML (`context.sources`)
- Tạo **context packet** (Markdown có header, sha256, size, truncation notice)
- Tạo **context manifest** (JSON với source URI, version, missing required)
- Lưu cả hai vào Postgres (`harness_artifacts`)
- Inject context packet vào mọi agent prompt

**Contract YAML:**
```yaml
context:
  max_file_bytes: 50000
  max_total_bytes: 250000
  sources:
    - path: "CLAUDE.md"
      role: target-guidance
      required: true
    - path: "docs/input/**/*.md"
      role: requirements
      required: true
    - path: "docs/technical_architecture.md"
      role: architecture
      required: false
```

**Gate H1:**
- `json_no_missing_required` — fail nếu required source không tồn tại
- `db_artifact_exists` — fail nếu context packet chưa được lưu vào DB

**Còn thiếu (backlog):**
- Per-phase context contract thay vì dùng chung một packet toàn run
- Context freshness check (phát hiện tài liệu quá cũ)
- Permission-aware retrieval khi có nhiều tenant/project

---

### H2 — Tool Harness

**Mục tiêu:** Kiểm soát tool nào agent được dùng. Agent không gọi tool ngoài allowlist.

**Cách hoạt động hiện tại:**
- `allowed_tools` khai báo trong adapter YAML → truyền vào `claude --allowedTools`
- Slash command inlining: `_inline_project_command()` đọc `.claude/commands/*.md` → nhúng vào prompt cho Codex (không có native slash command)
- Agent definition inlining: resolve `subagent_type` → nhúng `.claude/agents/*.md`

**Contract YAML:**
```yaml
agent:
  provider: claude          # claude | codex | (tương lai: copilot, internal)
  bin: claude
  model: sonnet
  max_turns: 40
  max_budget_usd: 5.0
  allowed_tools: "Read,Write,Edit,Bash,Glob,Grep"
  skip_permissions: true    # chỉ trong sandbox
  prompt_pack:
    command_dirs:
      - target:.claude/commands
      - commands
    agent_dirs:
      - target:.claude/agents
```

**Còn thiếu (backlog):**
- Command allow/deny enforcement trước mọi shell gate (H2 policy chưa hard-enforce)
- MCP server adapter (cho Copilot và Claude với MCP tools)
- Rate limiting và idempotency key cho write tool calls
- Dry-run mode cho action rủi ro cao

---

### H3 — Evaluation Harness

**Mục tiêu:** Gate deterministic sau mỗi phase. Agent có thể sinh output, nhưng gate quyết định pass/fail.

**Gate types hiện có:**

| Type | Mô tả |
|---|---|
| `shell` | Chạy shell command, pass nếu exit 0 |
| `glob_nonempty` | Pass nếu tìm thấy ít nhất 1 file khớp pattern |
| `no_markers` | Pass nếu không tìm thấy forbidden marker trong file |
| `agent_output` | Pass nếu agent output không chứa fail_markers |
| `secret_scan` | Pass nếu không phát hiện secret trong context/output |
| `json_no_missing_required` | Pass nếu context manifest không có missing required |
| `db_artifact_exists` | Pass nếu artifact ID tồn tại trong Postgres |

**Contract YAML:**
```yaml
phases:
  - name: implement
    command: "/speckit.implement {feature}"
    max_attempts: 3
    gates:
      - name: build-pass
        type: shell
        params:
          cmd: "npm run build"
      - name: no-todo-markers
        type: no_markers
        params:
          glob: "**/*.ts"
          markers: ["TODO:", "FIXME:", "NOT IMPLEMENTED"]
      - name: tests-pass
        type: shell
        params:
          cmd: "npm test -- --passWithNoTests"
```

**Còn thiếu (backlog):**
- LLM-as-judge gate (đánh giá requirement, design, review dạng ngôn ngữ)
- Coverage gate (minimum test coverage threshold)
- API compatibility gate (breaking change detection)

---

### H4 — Security Harness

**Mục tiêu:** Không để secret, credential hoặc unsafe content vào context packet hoặc agent output.

**Cách hoạt động hiện tại:**
- `secret_scan` gate: regex pattern match trên context sources và agent output
- Scan trước khi đưa context vào agent (H4-context-security phase)
- Scan sau khi agent sinh code (H4-generated-security phase)

**Còn thiếu (backlog):**
- Tích hợp Gitleaks/TruffleHog thay thế/bổ sung regex
- Prompt injection detection
- PII/DLP redaction trước khi inject context
- Dependency/SCA scan (Dependabot / OSV-Scanner)

---

### H5 — Governance Harness

**Mục tiêu:** Quản lý retry, escalation và approval boundary khi phase fail.

**Cách hoạt động hiện tại:**
- `max_attempts` per phase (config YAML)
- Nếu hết attempt → `escalate()` → lưu escalation artifact vào Postgres → exit với error code
- Repair loop: nếu gate fail và còn attempt → inject failure report vào prompt → resume cùng session

**Contract YAML:**
```yaml
phases:
  - name: implement
    max_attempts: 3   # 3 lần tự repair trước khi escalate
```

**Escalation artifact ghi vào Postgres:**
```json
{
  "type": "escalation",
  "phase": "implement",
  "reason": "gate failed after 3 attempts",
  "gate_report": "..."
}
```

**Còn thiếu (backlog):**
- Approval workflow tích hợp (Slack/Teams/email notification khi escalate)
- Risk classification theo domain (payment, auth, infra)
- Human override với required reason + audit
- Policy engine (OPA/Rego) cho approval decision

---

### H6 — AgentOps Harness

**Mục tiêu:** Lưu toàn bộ run data để dashboard có thể quan sát, debug và replay.

**Schema Postgres hiện có:**

| Table | Vai trò |
|---|---|
| `harness_runs` | Run metadata: feature, provider, target, mode, status, cost_usd, pid |
| `harness_run_state` | State JSON resumable của run hiện tại |
| `harness_artifacts` | Context packets, manifests, phase logs, gate logs, escalations |
| `phase_events` | Timeline start/done của từng phase attempt |
| `gate_outcomes` | Pass/fail record của từng gate |
| `run_events` | General event stream cho dashboard và audit |

**Metrics có sẵn:**
- `cost_usd` per run (tổng hợp từ provider response)
- `attempts` per phase
- `gate_result` per phase attempt
- Phase timeline (started_at, finished_at)

**Còn thiếu (backlog):**
- Token count, latency p95 per provider call
- Drift detection (quality score giảm theo thời gian)
- OpenTelemetry trace export
- Langfuse/LangSmith integration cho LLM-specific observability
- Cost alert khi vượt threshold

---

### H7 — Orchestration Harness

**Mục tiêu:** Chạy phase graph, resume sau crash, repair với feedback, hai mode expanded/boss.

**Cách hoạt động hiện tại:**

```python
for phase in cfg.phases:
    if phase đã done (resume): skip
    if phase.skip_if_exists và file exists: skip

    for attempt in range(1, max_attempts + 1):
        # Lần đầu: chạy phase.command
        # Lần sau: inject failure report + resume same session (repair loop)
        res = agent_runner.run(...)
        outcomes = gates_mod.run_gates(...)
        if all pass: break
        feedback = failure_report

    if not passed:
        escalate()
        return error_code

state["status"] = "complete"
```

**Hai mode:**

*Expanded mode:*
```
H1-context → H4-context-security → system-srs → srs → basic-design →
specify → clarify → review-spec → plan → review-plan → detail-design →
generate-tests → tasks → implement → review-code → run-tests →
H4-generated-security → verify-launch
```

*Boss mode:*
```
H1-context → H4-context-security → /okr.bossbuiltin (13-step internal) →
H4-generated-security → build/test/acceptance gates
```

**Còn thiếu (backlog):**
- Parallel phase execution (bước độc lập chạy song song)
- Workflow versioning (task cũ vẫn chạy theo definition cũ)
- Compensating action khi tool có side effect cần rollback

---

## 7. Target Adapter Pattern

Mọi dự án muốn dùng harness chỉ cần tạo một file YAML. Harness engine không thay đổi.

### Cấu trúc adapter file

```yaml
# packages/ai-harness/targets/<target-id>/harness.<target>.yaml

target:
  id: my-project
  name: My Project

context:
  max_file_bytes: 50000
  max_total_bytes: 250000
  sources:
    - path: "CLAUDE.md"
      role: target-guidance
      required: true
    - path: "docs/input/**/*.md"
      role: requirements
      required: true

agent:
  provider: claude          # claude | codex
  model: sonnet
  max_turns: 40
  max_budget_usd: 5.0
  allowed_tools: "Read,Write,Edit,Bash,Glob,Grep"
  skip_permissions: true
  prompt_pack:
    command_dirs:
      - target:.claude/commands
      - commands
    agent_dirs:
      - target:.claude/agents

project:
  build: "npm run build"
  test: "npm test -- --passWithNoTests"
  lint: "npm run lint"
  security: "npm audit --audit-level=high"

specs_glob: "specs/*"
state_dir: ".specify/state"
runs_dir: ".specify/runs"

phases:
  - name: H1-context
    command: null           # gate-only, không gọi agent
    max_attempts: 1
    gates:
      - name: context-manifest-exists
        type: db_artifact_exists
        params:
          id_key: context_manifest_id
      - name: no-missing-required
        type: json_no_missing_required
        params: {}

  - name: specify
    command: "/speckit.specify {feature}"
    max_attempts: 3
    gates:
      - name: spec-files-exist
        type: glob_nonempty
        params:
          glob: "specs/**/*.md"

  - name: implement
    command: "/speckit.implement {feature}"
    max_attempts: 3
    gates:
      - name: build-pass
        type: shell
        params:
          cmd: "${project.build}"
      - name: tests-pass
        type: shell
        params:
          cmd: "${project.test}"
```

### Thêm target mới

```
1. Tạo packages/ai-harness/targets/<target-id>/harness.<target>.yaml
2. Khai báo context.sources trỏ vào tài liệu của target project
3. Map các phase → slash command trong target's .claude/commands/
4. Định nghĩa gate cho từng phase
5. Thêm target vào harness/targets/<target-id>/target.yaml (registry)
```

---

## 8. Provider Abstraction

Harness tách provider logic ra khỏi orchestration. Mọi provider phải implement interface sau (thông qua `agent_runner.run()`):

```python
@dataclass
class AgentResult:
    ok: bool            # True nếu agent hoàn thành không lỗi
    text: str           # Output text của agent
    session_id: str     # Session ID để resume (nếu provider hỗ trợ)
    cost: float         # Chi phí USD của lần gọi này
    raw: object         # Raw response để debug
```

### Provider hiện có

| Provider | Status | Cách gọi |
|---|---|---|
| `claude` | Hoàn chỉnh | `claude -p <prompt> --output-format json --max-turns N` |
| `codex` | Hoàn chỉnh | `codex exec <prompt> --json`, slash command inlining |

### Thêm provider mới

```python
# packages/ai-harness/src/tool/agent_runner.py

def run(agent_cfg, prompt, resume_session=None, cwd=".") -> AgentResult:
    provider = agent_cfg.provider.lower()
    if provider == "claude":  return _run_claude(...)
    if provider == "codex":   return _run_codex(...)
    if provider == "copilot": return _run_copilot(...)  # thêm mới
    if provider == "internal": return _run_internal(...) # thêm mới
```

### Kế hoạch provider tương lai

| Provider | Cách tích hợp | Priority |
|---|---|---|
| GitHub Copilot | GitHub Issues API + Actions trigger | Medium |
| Internal LangGraph agent | Direct Python call, không subprocess | Medium |
| Copilot custom agent | GitHub agent API | Low |
| OpenAI Codex Cloud | REST API | Low |

---

## 9. End-to-End Test Target: OKR App

`AINative_OKR_Claude_GHCP/` là target đầu tiên dùng để kiểm chứng harness hoạt động end-to-end. Nó là prompt pack hoàn chỉnh, không bị sửa.

### Điều kiện "harness đạt" với target OKR

```
✅ H1 context packet được build và lưu vào Postgres
✅ H4 secret scan không phát hiện credential trong context
✅ Phase system-srs chạy và sinh SRS artifact
✅ Phase srs, basic-design, specify, plan, detail-design chạy và pass gate
✅ Phase implement sinh code FE (React) + BE (NestJS/Python)
✅ Gate build pass: npm run build / python -m pytest
✅ Gate tests pass: ít nhất basic test suite
✅ Phase review-code, run-tests chạy và gate pass
✅ H4 generated-security scan không phát hiện secret trong code
✅ Dashboard hiển thị đầy đủ phase timeline, gate outcomes, cost
✅ Run có thể resume từ phase cuối nếu crash giữa chừng
```

### Run command

```powershell
# Expanded mode
$env:PYTHONPATH = "packages/ai-harness/src"
python -m cli run `
  --repo .\AINative_OKR_Claude_GHCP `
  --config .\packages\ai-harness\targets\okr-ghcp\harness.okr.yaml `
  --feature "Build the OKR web application" `
  --tech-stack "React 18 + NestJS 10 + Prisma 5 + MySQL 8 + Docker"

# Boss mode
python -m cli run `
  --repo .\AINative_OKR_Claude_GHCP `
  --config .\packages\ai-harness\targets\okr-ghcp\harness.okr.boss.yaml `
  --feature "Build the OKR web application"
```

---

## 10. Dashboard Flow

```
User mở browser → React UI
  → Chọn: target (okr-ghcp), provider (claude/codex), mode (expanded/boss)
  → Nhập: feature description, tech stack
  → POST /api/harness-runs
  → Backend spawn: python -m cli run ...
  → Harness ghi state/events vào Postgres
  → Frontend poll: GET /api/harness-runs/{id} mỗi 3s
  → Hiển thị: phase timeline, gate outcomes, cost, artifacts, logs
  → Nếu escalate: hiển thị failure report để user debug
```

### API endpoints hiện có (FastAPI)

| Endpoint | Mục đích |
|---|---|
| `GET /api/targets` | Danh sách target adapter available |
| `POST /api/harness-runs` | Tạo và khởi động run mới |
| `GET /api/harness-runs` | Danh sách run gần nhất |
| `GET /api/harness-runs/{id}` | Chi tiết run: phases, gates, cost |
| `GET /api/harness-runs/{id}/artifacts` | Artifacts của run |
| `GET /api/harness-runs/{id}/events` | Event stream của run |

---

## 11. Trạng Thái Hiện Tại & Backlog

### Đã hoàn thành

| Thành phần | Trạng thái |
|---|---|
| H7 Phase orchestrator (loop, retry, repair, resume) | ✅ Hoàn chỉnh |
| H2 Claude Code adapter | ✅ Hoàn chỉnh |
| H2 Codex CLI adapter | ✅ Hoàn chỉnh |
| H2 Slash command inlining cho Codex | ✅ Hoàn chỉnh |
| H1 Context packet + manifest builder | ✅ Hoàn chỉnh |
| H3 Gate types: shell, glob, no_markers, agent_output, secret_scan, db_artifact | ✅ Hoàn chỉnh |
| H4 Basic secret scan | ✅ Hoàn chỉnh |
| H5 Escalation với Postgres artifact | ✅ Hoàn chỉnh |
| H6 Postgres schema và persistence | ✅ Hoàn chỉnh |
| H6 Phase/gate event logger | ✅ Hoàn chỉnh |
| OKR expanded mode adapter (`harness.okr.yaml`) | ✅ Hoàn chỉnh |
| OKR boss mode adapter (`harness.okr.boss.yaml`) | ✅ Hoàn chỉnh |
| OKR fallback command wrappers (okr.bd, okr.dd, okr.reviewplan, okr.testkit) | ✅ Hoàn chỉnh |
| Dashboard backend: FastAPI + Postgres | ✅ Hoàn chỉnh |
| Dashboard frontend: React run observation UI | ✅ Hoàn chỉnh |
| Target/mode selection trong dashboard | ✅ Hoàn chỉnh |

### Backlog (ưu tiên)

| Item | Layer | Priority |
|---|---|---|
| H2 command allow/deny enforcement trước shell gate | H2 | High |
| H4 Gitleaks/TruffleHog integration (thay regex) | H4 | High |
| H4 Prompt injection detection baseline | H4 | High |
| Test end-to-end: chạy harness với OKR target, verify FE+BE sinh ra | H7 | High |
| H1 Per-phase context contract | H1 | Medium |
| H1 Context freshness check | H1 | Medium |
| H6 Token count + latency per provider call | H6 | Medium |
| H6 Cost alert khi vượt threshold | H6 | Medium |
| H5 Approval workflow notification (Slack/email) | H5 | Medium |
| H3 LLM-as-judge gate cho requirement/design artifact | H3 | Medium |
| H2 MCP server adapter | H2 | Medium |
| H7 Parallel phase execution | H7 | Low |
| H5 OPA/Rego policy engine | H5 | Low |
| Provider: GitHub Copilot adapter | H2 | Low |
| Provider: Internal LangGraph adapter | H2 | Low |

---

## 12. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Resumability** | Run state phải survive harness process crash; resume từ phase gần nhất |
| **Idempotency** | Retry không tạo duplicate artifact (cùng run_id + phase + attempt là unique) |
| **Provider swap** | Đổi `provider: claude` → `provider: codex` trong YAML, không sửa code |
| **Target swap** | Đổi `--config` arg, không sửa harness engine |
| **Security** | Secret không xuất hiện trong prompt log, artifact content hoặc context packet |
| **Cost control** | `max_budget_usd` per agent call; tổng cost_usd được track per run |
| **Observability** | 100% phase có event trong Postgres; 100% gate có pass/fail record |
| **Audit** | Mọi agent call có prompt snippet lưu trong `phase_events` |
| **Portability** | Harness engine là pure Python, chạy được trên macOS/Linux/Windows với PATH provider binary |

---

## 13. Quy Ước Phát Triển

- Không sửa `AINative_OKR_Claude_GHCP/` trừ khi fix nội dung prompt pack.
- Adapter YAML sống trong `packages/ai-harness/targets/<id>/`, không sống trong target folder.
- Mọi SDLC artifact sinh ra trong run phải lưu vào Postgres, không ghi thêm file state/log local.
- Gate mới phải thêm vào `evaluation/gates.py` và khai báo type string rõ ràng.
- Provider adapter mới phải return `AgentResult` với đầy đủ 5 trường.
- Không thêm ORM; dùng psycopg2 trực tiếp với SQL rõ ràng.
- Tài liệu chính là file này (`docs/REQUIREMENTS.md`); các file khác trong `docs/` là tài liệu bổ sung.
