# Next Steps — AI Harness + OKR Claude/GHCP Integration

> Cập nhật: 2026-06-30

---

## Mục tiêu

Chạy bộ prompt 13 bước của `AINative_OKR_Claude_GHCP/` thông qua dashboard AI Harness, với **Claude Code** làm provider. Mỗi step được log vào PostgreSQL, UI hiển thị realtime từng phase đang chạy, output của Claude và log hệ thống.

---

## Kiến trúc tổng quan

```text
Dashboard UI (React)
    ↕ polling 3s (REST API)
FastAPI Backend  ←→  PostgreSQL
    ↓ spawn subprocess
Python Harness CLI  (packages/ai-harness/src/)
    ↓ per phase
claude -p "..." --output-format stream-json
    ↓ JSONL events streamed line-by-line
DB: run_events table  →  UI: Events tab
Harness stdout        →  log file  →  UI: System Log tab
```

**Target config:** `packages/ai-harness/targets/okr-ghcp/harness.okr.yaml` — 16 phase:
`H1-context` → `H4-context-security` → `system-srs` → `srs` → `basic-design` → `specify` → `clarify` → `review-spec` → `plan` → `review-plan` → `detail-design` → `generate-tests` → `tasks` → `implement` → `review-code` → `run-tests` → `H4-generated-security` → `verify-launch`

**Boss mode** (`harness.okr.boss.yaml`): 1 phase duy nhất gọi `okr.bossbuiltin` — agent tự điều phối toàn bộ 13 step bên trong.

---

## Những gì đã làm trong session này

### Gap analysis (rà soát)

Đã đọc và phân tích toàn bộ:

- `AINative_OKR_Claude_GHCP/` — 13-step pipeline, agents, protocols, step definitions
- `packages/ai-harness/src/` — orchestrator, agent_runner, db_logger, gates, config
- `apps/dashboard/backend/app/main.py` — FastAPI, subprocess management, DB logging
- `apps/dashboard/frontend/src/` — React pages, shared hooks/components

### Gaps tìm thấy

| # | Gap | Vấn đề |
| --- | --- | --- |
| 1 | `agent_runner.py` | `subprocess.run(capture_output=True)` blocking hoàn toàn — không có output real-time |
| 2 | `orchestrator.py` | Không truyền `run_id`/`phase_name` vào agent_runner → không tag được events |
| 3 | `agentops/db_logger.py` | Không có hàm ghi Claude streaming events vào DB |
| 4 | `main.py` | Thiếu endpoint đọc raw log file của subprocess |
| 5 | `shared.jsx` | `PHASE_META` thiếu 7 phase name thực tế: `review-spec`, `review-plan`, `review-code`, `run-tests`, `generate-tests`, `H4-generated-security`, `verify-launch` |
| 6 | `Execute.jsx` | Default provider = `codex`, không phải `claude` |
| 7 | `shared.jsx` | `RunOutputPanel` chỉ có 1 view events, không có System Log tab |

### Code đã thay đổi

**`packages/ai-harness/src/agentops/db_logger.py`**

- Thêm hàm `log_stream_event(run_id, phase_name, event)` — nhận một JSON event từ Claude streaming, phân loại (`assistant`/`tool_use`/`tool_result`/`result`) và ghi vào bảng `run_events`.

**`packages/ai-harness/src/tool/agent_runner.py`**

- Thêm param `run_id` và `phase_name` vào `run()` và `_run_claude()`
- Đổi từ `subprocess.run(capture_output=True)` → `subprocess.Popen(stdout=PIPE, bufsize=1)`
- Dùng `--output-format stream-json` thay vì `--output-format json`
- Đọc stdout line-by-line: echo ra harness stdout (vào file log) + gọi `log_stream_event()` cho từng event
- Parse result từ event có `"type": "result"` thay vì parse single JSON blob

**`packages/ai-harness/src/orchestration/orchestrator.py`**

- Truyền `run_id=run_id, phase_name=phase.name` vào cả 2 lần gọi `agent_runner.run()` (attempt 1 và repair attempt)

**`apps/dashboard/backend/app/main.py`**

- Thêm endpoint `GET /api/harness-runs/{run_id}/log?lines=200` — đọc tail của file log subprocess bằng hàm `_tail()` có sẵn

**`apps/dashboard/frontend/src/shared.jsx`**

- `PHASE_META`: thêm đủ tất cả phase name từ `harness.okr.yaml` và `harness.okr.boss.yaml`
- `EVENT_TYPE_LABELS`: thêm các loại event mới `claude_text`, `claude_tool`, `claude_tool_result`, `claude_done`, `claude_raw`, `escalated`
- Thêm hook `useLogTail(runId)` — poll `/api/harness-runs/{id}/log` mỗi 3s
- `RunOutputPanel`: thêm 2-tab switcher (**Events** / **System Log**), dùng `useLogTail` cho tab System Log

**`apps/dashboard/frontend/src/pages/Execute.jsx`**

- `useState('codex')` → `useState('claude')` (default provider)

**`apps/dashboard/frontend/src/styles.css`**

- Thêm CSS cho `.dp-tabs`, `.dp-tab`, `.dp-tab--active`, `.dp-tab-badge`, `.dp-raw-log`, `.rawLogLine`

### Kết quả verify

```bash
python -m compileall packages/ai-harness/src/tool/agent_runner.py \
  packages/ai-harness/src/orchestration/orchestrator.py \
  packages/ai-harness/src/agentops/db_logger.py \
  apps/dashboard/backend/app/main.py
# → không lỗi

cd apps/dashboard/frontend && npm run build
# → ✓ built in 7.80s  (402 kB JS, 39 kB CSS)
```

---

## Trạng thái hiện tại

Code đã fix xong, build pass. **Chưa chạy được thực tế** — cần hoàn thiện các bước dưới đây.

---

## 1. Thiết lập môi trường (prerequisites)

### 1.1 PostgreSQL

Backend cần một PostgreSQL instance đang chạy. Chọn một trong hai:

```bash
# Option A — Docker (đơn giản nhất)
docker run -d --name harness-pg \
  -e POSTGRES_USER=harness \
  -e POSTGRES_PASSWORD=harness_dev \
  -e POSTGRES_DB=harness \
  -p 5432:5432 \
  postgres:16-alpine

# Option B — dùng docker-compose nếu có sẵn postgres service
docker compose up -d postgres
```

### 1.2 Biến môi trường backend

Tạo file `apps/dashboard/backend/.env`:

```env
DATABASE_URL=postgresql://harness:harness_dev@localhost:5432/harness
```

### 1.3 Xác nhận Claude Code CLI đã cài và authenticated

```bash
claude --version          # cần >= 1.x
claude -p "ping" --output-format stream-json   # test streaming
```

Nếu chưa đăng nhập:

```bash
claude login
```

---

## 2. Khởi động dashboard

```bash
# Terminal 1 — Backend
cd apps/dashboard/backend
./start.sh
# hoặc: uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd apps/dashboard/frontend
npm run dev
# → http://localhost:5173
```

Kiểm tra backend healthy:

```bash
curl http://localhost:8000/health     # → {"ok": true}
curl http://localhost:8000/api/harness-targets  # phải thấy okr-ghcp
```

---

## 3. Chạy thử một run

1. Mở `http://localhost:5173/execute`
2. Điền feature description (ví dụ: *"Build OKR web app from existing requirements"*)
3. Provider = **Claude Code**, Mode = **Expanded**
4. Click **Start Run**
5. Dashboard tự navigate sang `/pipeline/{runId}`

Trên Pipeline page:

- Cột trái: flow graph các phase với trạng thái live
- Cột phải: tab **Events** (DB events từ Claude) và **System Log** (raw subprocess log)

---

## 4. Các vấn đề có thể gặp khi chạy lần đầu

### 4.1 H1-context phase fail — context sources missing

`harness.okr.yaml` yêu cầu các file này tồn tại trong `AINative_OKR_Claude_GHCP/`:

- `.specify/memory/constitution.md` ✅ có sẵn
- `docs/input/okr-requirement.md` ✅ có sẵn
- `docs/technical_architecture.md` ✅ có sẵn
- `.claude/agents/protocols/*.md` ✅ có sẵn
- `.claude/agents/steps/*.md` ✅ có sẵn

Gate `context-packet-exists` dùng `db_artifact_exists` — yêu cầu `context builder` lưu artifact ID vào DB. Nếu gate này fail, kiểm tra `HARNESS_DB_URL` có được set đúng không trong subprocess env (xem `main.py` line ~344).

### 4.2 `--output-format stream-json` không được hỗ trợ

Nếu Claude Code version cũ không support flag này, harness sẽ trả về lỗi ngay lập tức. Fix:

```python
# Trong agent_runner.py, đổi lại về json nếu cần fallback:
"--output-format", "json",  # blocking nhưng stable
```

Hoặc upgrade Claude Code:

```bash
npm install -g @anthropic-ai/claude-code@latest
```

### 4.3 `claude` không tìm thấy trong PATH của subprocess

Backend chạy subprocess `python -m cli run ...`, subprocess đó gọi `claude`. Đảm bảo `claude` trong PATH của session mà backend chạy:

```bash
which claude    # phải có output
echo $PATH      # kiểm tra PATH khi backend start
```

### 4.4 Gate `implement` fail ngay (build/typecheck/lint)

Phase `implement` trong `harness.okr.yaml` có gate `shell` chạy `docker compose build`, `typecheck`, `lint`, `test`. Lần đầu tiên chạy khi chưa có source code thì chắc chắn fail. Đây là expected behavior — agent sẽ generate code rồi retry.

Nếu Docker không chạy → các gate shell sẽ fail → phase bị escalate. Cần đảm bảo Docker daemon đang chạy trước khi bắt đầu phase `implement`.

---

## 5. Cải thiện tiếp theo (backlog)

| Ưu tiên | Hạng mục | Mô tả |
| --- | --- | --- |
| 🔴 Cao | SSE / WebSocket | Thay polling 3s bằng server-sent events cho log real-time thực sự |
| 🔴 Cao | `harness.okr.yaml` provider default | Tạo thêm `harness.okr.claude.yaml` với `provider: claude` để tránh phụ thuộc vào CLI flag |
| 🟡 Trung bình | Boss mode validation | Test `harness.okr.boss.yaml` — chạy toàn bộ 13 step qua `okr.bossbuiltin` |
| 🟡 Trung bình | Log search / filter | Thêm filter theo event_type (CLAUDE, GATE, TOOL...) trên Event tab |
| 🟡 Trung bình | Artifact viewer | Click vào artifact để xem nội dung file `.md` ngay trong UI |
| 🟢 Thấp | Cost tracking | Hiển thị cost tích lũy real-time trên Pipeline header (đã có trong DB) |
| 🟢 Thấp | Resume run | UI button để resume run bị dừng giữa chừng (CLI đã hỗ trợ `resume`) |
| 🟢 Thấp | Multi-run comparison | So sánh 2 run cùng feature để đánh giá cải thiện |

---

## 6. Luồng kiểm tra nhanh (smoke test)

```bash
# 1. Khởi động stack
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=harness_dev -e POSTGRES_USER=harness -e POSTGRES_DB=harness postgres:16-alpine
cd apps/dashboard/backend && DATABASE_URL=postgresql://harness:harness_dev@localhost:5432/harness uvicorn app.main:app --port 8000 &
cd apps/dashboard/frontend && npm run dev &

# 2. Tạo run test (boss mode ngắn hơn để test nhanh)
curl -X POST http://localhost:8000/api/harness-runs \
  -H "Content-Type: application/json" \
  -d '{"feature":"Test OKR pipeline","provider":"claude","mode":"boss","target":"okr-ghcp"}'

# 3. Theo dõi events
curl "http://localhost:8000/api/harness-runs/<RUN_ID>/events"
curl "http://localhost:8000/api/harness-runs/<RUN_ID>/log"
```

---

## 7. Files thay đổi trong session này

```text
packages/ai-harness/src/tool/agent_runner.py        ← streaming Popen
packages/ai-harness/src/orchestration/orchestrator.py ← pass run_id/phase
packages/ai-harness/src/agentops/db_logger.py        ← log_stream_event()
apps/dashboard/backend/app/main.py                   ← /log endpoint
apps/dashboard/frontend/src/shared.jsx               ← PHASE_META, useLogTail, tabs
apps/dashboard/frontend/src/pages/Execute.jsx         ← default provider=claude
apps/dashboard/frontend/src/styles.css               ← dp-tabs, rawLogLine styles
```
