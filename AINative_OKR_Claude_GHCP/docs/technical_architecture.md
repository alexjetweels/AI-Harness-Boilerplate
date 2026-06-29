# Technical Architecture — OKR Web Application

**Version:** 1.0.0  
**Purpose:** Defines the system technical architecture optimized for Docker-based local development.  
**Target Team Size:** 3–5 developers  
**Environment:** Localhost-first, internal system, not public internet

---

## I. Technology Stack

### 1. Frontend

| Technology | Version | Role |
|------------|---------|------|
| React | 18.x | UI framework |
| Vite | 5.x | Build tool & dev server with HMR |
| React Router DOM | 6.x | Client-side routing |
| TanStack Query (React Query) | 5.x | Server state management, caching |
| Axios | 1.x | HTTP client with interceptors |
| React Hook Form | 7.x | Form state and submission |
| Zod | 3.x | Schema validation (shared with backend types) |
| Tailwind CSS | 3.x | Utility-first styling |

**Decisions:**

- **Vite** over Create React App: significantly faster HMR in Docker dev mode via volume mounts.
- **TanStack Query** for server state: eliminates manual loading/error state boilerplate for API calls.
- **React Router DOM v6** is sufficient for this internal SPA — no SSR needed.
- **Error boundary:** A single `<AppErrorBoundary>` wraps the router root. API errors are caught at the TanStack Query layer with a global `onError` handler; only component crashes bubble to the boundary.
- **Form validation:** Zod schemas defined in a shared `src/schemas/` directory; used by React Hook Form's `zodResolver` on the frontend and replicated for backend DTOs, ensuring consistent validation rules.

---

### 2. Backend

| Technology | Version | Role |
|------------|---------|------|
| Node.js | 20 LTS | Runtime |
| NestJS | 10.x | Application framework |
| Prisma | 5.x | ORM, schema management, migrations |
| @nestjs/jwt | latest | JWT sign/verify (no Passport — Username/Password only, no SSO) |
| bcrypt | 5.x | Password hashing |
| class-validator + class-transformer | latest | DTO validation |
| @nestjs/swagger | 7.x | OpenAPI / Swagger UI |
| dotenv / @nestjs/config | — | ~~Not used~~ — values hardcoded (workshop) |

**Decisions:**

- **NestJS over Express:** For a 3–5 person team, NestJS's module/controller/service structure enforces consistent code organisation without custom conventions. Decorators (`@Get`, `@UseGuards`, `@Body`) reduce boilerplate.
- **Prisma over TypeORM:** Prisma's `schema.prisma` is a single source of truth for DB schema, migrations, and type generation. The generated client provides full type-safety. TypeORM entities and migrations drift more easily.
- **JWT only (no session store):** Stateless authentication is appropriate for an internal tool. Access token TTL = 1h, refresh token TTL = 7d, stored in HttpOnly cookies.
- **No env files (workshop):** All configuration values (DB credentials, JWT secret, ports) are hardcoded directly in `docker-compose.yml` and application config. No `.env` file or `@nestjs/config` needed.
- **Swagger:** Auto-generated from NestJS decorators; available at `/api/docs` in dev environment only.

---

### 3. Database

| Technology | Version | Role |
|------------|---------|------|
| MySQL | 8.0 | Primary relational database |
| Prisma Migrate | 5.x | Schema migration engine |
| Prisma Studio | 5.x | GUI for DB inspection (dev only) |

**Decisions:**

- **MySQL 8.x:** Required by constraint. Uses `mysql2` driver via Prisma.
- **Migration strategy:** `prisma migrate dev` generates versioned SQL migration files under `prisma/migrations/`. Applied automatically on container start via entrypoint script.
- **Index strategy:** Primary keys on all tables. Composite index on `(objective_id, deadline)` for Key Result queries. Index on `user.email` for login lookups.
- **Authentication plugin:** MySQL is started with `--default-authentication-plugin=mysql_native_password` for compatibility with the `mysql2` driver.
- **Connection pooling:** Prisma's built-in connection pool, configured via `DATABASE_URL` parameter `connection_limit=10`. Sufficient for local dev and small team.
- **Volume persistence:** Named Docker volume `mysql_data` persists across `docker-compose up/down`. Destroyed only by `docker-compose down -v` (explicit reset).
- **Dev vs production:** Single `schema.prisma` file. All environment-specific values are set directly in `docker-compose.yml`. No separate `.env` files.

---

## II. Repository Structure (Monorepo)

```
okr-web/
├── backend/                    # NestJS API service
│   ├── src/
│   │   ├── main.ts             # Bootstrap, Swagger, global pipes
│   │   ├── app.module.ts       # Root module
│   │   ├── auth/               # JWT auth module
│   │   ├── users/              # User CRUD module
│   │   ├── objectives/         # Objective module
│   │   ├── key-results/        # Key Result module
│   │   └── common/             # Guards, filters, interceptors, decorators
│   ├── prisma/
│   │   ├── schema.prisma       # DB schema (single source of truth)
│   │   ├── migrations/         # Auto-generated migration SQL files
│   │   └── seed.ts             # Mock data seeding script
│   ├── test/                   # Jest integration tests
│   ├── .env.example            # (not used — values hardcoded for workshop)
│   ├── Dockerfile
│   └── package.json
│
├── frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── main.tsx            # React root
│   │   ├── App.tsx             # Router setup + error boundary
│   │   ├── pages/              # Route-level components
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── OKRDetail.tsx
│   │   │   ├── CreateObjective.tsx
│   │   │   └── KeyResultDetail.tsx
│   │   ├── components/
│   │   │   ├── layout/         # Sidebar, Header, AppLayout
│   │   │   └── ui/             # Button, Table, ProgressBar, Badge
│   │   ├── hooks/              # useAuth, useObjectives, useKeyResults
│   │   ├── lib/
│   │   │   ├── api.ts          # Axios instance, interceptors
│   │   │   └── queryClient.ts  # TanStack Query client config
│   │   ├── schemas/            # Zod validation schemas
│   │   └── types/              # TypeScript interfaces
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── package.json
│
├── database/
│   └── init/                   # (Unused at runtime; Prisma handles migration)
│
├── docker/
│   └── wait-for-db.sh          # Shell script: polls MySQL until ready
│
├── docs/                       # Architecture, SRS, BD, DD documents
│
├── docker-compose.yml          # Full stack orchestration (values hardcoded)
├── docker-compose.test.yml     # E2E test override (Playwright)
└── README.md
```

---

## III. Docker Compose Architecture (MANDATORY)

### Full `docker-compose.yml`

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: okr_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: okr_db
      MYSQL_USER: okr_user
      MYSQL_PASSWORD: okr_password
    command: --default-authentication-plugin=mysql_native_password
    ports:
      - '3307:3306'
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - okr_network
    healthcheck:
      test: ['CMD', 'mysqladmin', 'ping', '-h', 'localhost', '-u', 'root', '-prootpassword']
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: okr_backend
    restart: unless-stopped
    environment:
      DATABASE_URL: mysql://okr_user:okr_password@mysql:3306/okr_db
      JWT_SECRET: workshop_jwt_secret_key
      JWT_REFRESH_SECRET: workshop_jwt_refresh_secret_key
      PORT: 3000
    ports:
      - '3000:3000'
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - okr_network
    command: >
      sh -c "
        npx prisma migrate deploy &&
        npx prisma db seed &&
        npm run start:dev
      "

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: okr_frontend
    restart: unless-stopped
    environment:
      VITE_API_URL: http://localhost:3000
    ports:
      - '5173:5173'
    depends_on:
      - backend
    networks:
      - okr_network

  adminer:
    image: adminer:4
    container_name: okr_adminer
    restart: unless-stopped
    ports:
      - '8080:8080'
    depends_on:
      - mysql
    networks:
      - okr_network

volumes:
  mysql_data:
    driver: local

networks:
  okr_network:
    driver: bridge
```

### Container Startup Sequence

```
1. mysql starts → healthcheck polls mysqladmin ping
   - Uses mysql_native_password authentication plugin
   - Host port 3307 mapped to container port 3306
2. backend waits (depends_on: mysql condition: service_healthy)
3. backend command runs sequentially:
   a. npx prisma migrate deploy  → applies pending SQL migrations
   b. npx prisma db seed          → seeds mock data (idempotent)
   c. npm run start:dev           → starts NestJS with --watch
4. frontend starts → Vite dev server with HMR
   - API proxy configured via VITE_API_URL pointing to http://localhost:3000
5. adminer available at http://localhost:8080
```

### `docker/wait-for-db.sh`

> Not required when using `depends_on: condition: service_healthy`. Kept as a fallback utility:

```sh
#!/bin/sh
set -e

HOST=$1
PORT=$2
shift 2

until mysqladmin ping -h "$HOST" -P "$PORT" --silent; do
  echo "Waiting for MySQL at $HOST:$PORT..."
  sleep 2
done

exec "$@"
```

---

## IV. Mock Data Seeding Strategy

### Why Seeding is Required

- Developers need realistic OKR data on first container start (no manual data entry).
- E2E tests (Playwright) require a deterministic database state — random data breaks assertions.
- Onboarding new developers: `docker-compose up --build` produces a fully working system in one command.

### Seed Execution Rules

| Environment | Seed Runs? | Controlled By |
|-------------|------------|---------------|
| development | Always     | Hardcoded in entrypoint command |
| test        | Yes (reset before each E2E run) | `docker-compose.test.yml` override |

### Idempotency Pattern

The seed script uses `upsert` (Prisma's `createOrUpdate`) keyed on stable identifiers (email for users, slug for objectives). Running the seed twice produces no duplicates:

```typescript
// backend/prisma/seed.ts
import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  // Always seed — workshop environment, no env gate needed

  // --- Users ---
  const passwordHash = await bcrypt.hash('Password@123', 10);

  const admin = await prisma.user.upsert({
    where: { email: 'admin@okr.local' },
    update: {},
    create: { name: 'System Admin', email: 'admin@okr.local', password: passwordHash, role: 'ADMIN' },
  });

  const manager = await prisma.user.upsert({
    where: { email: 'manager@okr.local' },
    update: {},
    create: { name: 'Nguyen Van Manager', email: 'manager@okr.local', password: passwordHash, role: 'MANAGER' },
  });

  const employee = await prisma.user.upsert({
    where: { email: 'employee@okr.local' },
    update: {},
    create: { name: 'Nguyen Van A', email: 'employee@okr.local', password: passwordHash, role: 'EMPLOYEE' },
  });

  // --- Objectives ---
  const obj1 = await prisma.objective.upsert({
    where: { id: 1 },
    update: {},
    create: {
      title: 'POC AI for SQL Injection prevention',
      description: 'Evaluate AI tools for automated SQL injection detection',
      ownerId: employee.id,
      quarter: 'Q2/2026',
      status: 'IN_PROGRESS',
    },
  });

  const obj2 = await prisma.objective.upsert({
    where: { id: 2 },
    update: {},
    create: {
      title: 'AI for All: Upskill department members',
      description: 'Ensure all department members have practical AI skills',
      ownerId: manager.id,
      quarter: 'Q2/2026',
      status: 'NOT_STARTED',
    },
  });

  // --- Key Results ---
  await prisma.keyResult.upsert({
    where: { id: 1 },
    update: {},
    create: {
      objectiveId: obj1.id,
      title: 'Complete 3 POC sessions with security team',
      progress: 0,
      startValue: 0,
      targetValue: 3,
      deadline: new Date('2026-06-30'),
    },
  });

  await prisma.keyResult.upsert({
    where: { id: 2 },
    update: {},
    create: {
      objectiveId: obj2.id,
      title: 'AI for All members in department (100 people)',
      progress: 0,
      startValue: 0,
      targetValue: 100,
      deadline: new Date('2026-06-30'),
    },
  });

  console.log('Seed completed successfully.');
}

main()
  .catch((e) => { console.error(e); process.exit(1); })
  .finally(() => prisma.$disconnect());
```

### Seed Categories

| Category | Description | Sample Records |
|----------|-------------|----------------|
| Users | Admin, Manager, Employee accounts with hashed passwords | 3 users |
| Objectives | Sample OKRs per quarter | 2 objectives |
| Key Results | KRs linked to objectives with progress | 4 KRs |

### Database Reset

```bash
# Full reset: destroys volume (all data), rebuilds from scratch
docker-compose down -v && docker-compose up --build

# Soft reset: re-run seed only (keeps schema, replaces data)
docker-compose exec backend npx prisma db seed
```

### E2E Test Seed Isolation

`docker-compose.test.yml` overrides the backend command to always run seed before Playwright tests:

```yaml
# docker-compose.test.yml
services:
  backend:
    environment:
      SEED_ON_START: 'true'
    command: >
      sh -c "
        npx prisma migrate reset --force &&
        npx prisma db seed &&
        npm run start:prod
      "
```

---

## V. Local Development Flow

### First-Time Setup

```bash
git clone <repo-url>
cd okr-web
docker-compose up --build     # Builds all images, migrates DB, seeds, starts all services
```

After ~60 seconds:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:3000/api/v1 |
| Swagger UI | http://localhost:3000/api/docs |
| Adminer (DB GUI) | http://localhost:8080 |

Default login credentials (seeded):

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@okr.local | Password@123 |
| Manager | manager@okr.local | Password@123 |
| Employee | employee@okr.local | Password@123 |

### Hot Reload

- **Backend:** Source code is baked into the Docker image. Changes require `docker compose up --build backend` to rebuild.
- **Frontend:** Source code is baked into the Docker image. Changes require `docker compose up --build frontend` to rebuild.

### Configuration

- All values (DB credentials, JWT secrets, ports) are hardcoded in `docker-compose.yml` — no `.env` file required. This is intentional for the workshop environment.
- Frontend uses Vite's proxy (`vite.config.ts`): requests to `/api` are proxied to the backend service. The proxy target is configured via `VITE_API_URL` environment variable.

### Daily Developer Workflow

```bash
# Start everything
docker-compose up

# View logs for one service
docker-compose logs -f backend

# Open shell in container
docker-compose exec backend sh

# Reset DB and reseed
docker-compose down -v && docker-compose up

# Run specific migration
docker-compose exec backend npx prisma migrate dev --name add_comments_table
```

---

## VI. API Design Principles

### Conventions

- Base path: `/api/v1`
- Resource naming: plural nouns (`/objectives`, `/key-results`, `/users`)
- HTTP verbs: `GET` (read), `POST` (create), `PUT` (full update), `PATCH` (partial update), `DELETE`
- Auth: `Authorization: Bearer <token>` header on all protected routes

### Standard Response Envelope

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 45
  }
}
```

### Error Response Structure

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "title must not be empty",
    "details": [
      { "field": "title", "message": "title must not be empty" }
    ]
  }
}
```

### Pagination (Query Params)

```
GET /api/v1/objectives?page=1&limit=20&quarter=Q2%2F2026&ownerId=3
```

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/login | Login, returns access + refresh tokens |
| POST | /api/v1/auth/refresh | Refresh access token |
| GET | /api/v1/objectives | List objectives (filterable) |
| POST | /api/v1/objectives | Create objective |
| GET | /api/v1/objectives/:id | Get objective with KRs |
| PUT | /api/v1/objectives/:id | Update objective |
| POST | /api/v1/objectives/:id/key-results | Create KR under objective |
| PATCH | /api/v1/key-results/:id/progress | Update KR progress |
| GET | /api/v1/users | List users (Admin/Manager only) |

---

## VII. Authentication & Security

### JWT Flow

```
Login → POST /auth/login
  ↓
Backend validates credentials (bcrypt.compare)
  ↓
Issues accessToken (1h TTL) + refreshToken (7d TTL)
  ↓
Both stored as HttpOnly, SameSite=Strict cookies (not localStorage)
  ↓
Each request: JwtAuthGuard extracts token from cookie, validates signature
  ↓
On 401: Frontend calls POST /auth/refresh → new accessToken issued
```

### Security Measures

| Concern | Implementation |
|---------|---------------|
| Password hashing | bcrypt, cost factor 12 |
| SQL injection | Prisma parameterised queries (no raw SQL in application code) |
| JWT secret | Hardcoded in `docker-compose.yml` (workshop only — never do this in production) |
| CORS | `@nestjs/common` CORS configured to `http://localhost:5173` only |
| Role enforcement | `@Roles` decorator + `RolesGuard` on controller methods |
| Input validation | `class-validator` + `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true })` |
| Rate limiting | `@nestjs/throttler`, 60 req/min per IP on auth endpoints |
| Sensitive data | Passwords never returned in API responses (`@Exclude()` on password field) |

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| ADMIN | Full access to all resources and user management |
| MANAGER | View all objectives, approve/reject, view team members |
| EMPLOYEE | Create/edit own objectives, update own KR progress |

---

## VIII. Logging & Error Handling

### Backend Logging (Pino via nestjs-pino)

- All logs output as structured JSON (useful for future ELK/Loki integration)
- Request logging middleware logs: `method`, `url`, `statusCode`, `responseTimeMs`, `userId`
- Log levels: `error`, `warn`, `info`, `debug` (debug disabled in production)

```json
{
  "level": "info",
  "time": "2026-04-05T10:23:11.000Z",
  "reqId": "req-abc123",
  "method": "PATCH",
  "url": "/api/v1/key-results/3/progress",
  "statusCode": 200,
  "responseTimeMs": 34,
  "userId": 5
}
```

### Centralised Error Filter (NestJS)

A global `HttpExceptionFilter` catches all exceptions and maps them to the standard error envelope. Unhandled errors return HTTP 500 with `INTERNAL_SERVER_ERROR` code — stack traces logged server-side, never exposed to client.

### Frontend Error Boundary

```tsx
// src/App.tsx
<AppErrorBoundary fallback={<ErrorPage />}>
  <RouterProvider router={router} />
</AppErrorBoundary>
```

TanStack Query's `onError` global callback handles API error toasts without crashing the component tree.

---

## IX. Testing Strategy

### Backend (Jest)

- **Unit tests:** Services tested in isolation with Prisma mocked via `jest.mock`.
- **Integration tests:** `@nestjs/testing` spins up full NestJS app with SQLite in-memory database override.
- Test files co-located under `backend/test/`.

### Frontend

- **Component tests:** Vitest + React Testing Library for unit-level component behaviour.
- **No Storybook** for this scope — too much overhead for a 3–5 person team.

### E2E (Playwright)

- Tests live in `e2e/` directory at the project root.
- Playwright connects to the running `docker-compose.test.yml` stack.
- Each test suite calls `resetDb()` helper (hits a dev-only `/api/v1/test/reset` endpoint) to restore seed state.
- Scenarios cover: login, create objective, update KR progress, dashboard display.

```bash
# Run E2E tests
docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d
npx playwright test
```

### Coverage Targets

| Layer | Target |
|-------|--------|
| Backend service unit tests | ≥ 70% |
| Critical auth/KR flows | 100% integration coverage |
| E2E happy paths | All 5 screens covered |

---

## X. Scalability Considerations

While this is localhost-first, the architecture does not create dead-ends:

| Concern | Current Decision | Path to Scale |
|---------|-----------------|---------------|
| Database | Single MySQL container | Extract to managed RDS; Prisma `DATABASE_URL` is the only change |
| Auth | Stateless JWT | No server-side session store means horizontal scaling of backend is trivial |
| Frontend | SPA static build | `npm run build` output can be deployed to S3/CDN or served via Nginx |
| Config | Hardcoded in `docker-compose.yml` | Move to `.env` + `@nestjs/config`, then AWS Parameter Store / Vault |
| Migrations | `prisma migrate deploy` | Identical command in CI/CD pipeline — no code change needed |
| CI/CD | Not configured | GitHub Actions: `docker-compose -f docker-compose.test.yml up`, run tests, push image |

---

## XI. Architecture Rationale

### NestJS over plain Express

For 3–5 developers, NestJS enforces a module/controller/service structure that prevents the "spaghetti Express router" problem. The decorators and DI system make the codebase navigable without tribal knowledge. The trade-off is a slightly steeper learning curve (decorators, DI concepts), which is acceptable for a workshop project that may grow.

### Prisma over TypeORM

Prisma's `schema.prisma` is the single source of truth for the database schema. Migrations are generated automatically and are plain SQL files — reviewable in PRs. TypeORM requires manual synchronisation between entity decorators and migration files, which causes drift in team environments. Prisma's type-safe client also eliminates an entire class of runtime query errors.

### MySQL 8.x

Required by the constraint. MySQL 8 features (`ROW_NUMBER`, recursive CTEs, window functions) may be useful for reporting queries later. The `utf8mb4` charset handles Unicode (Vietnamese characters in objective titles).

### Docker Compose

All-in-one orchestration that requires zero local installation beyond Docker. A new developer runs one command and has a working system. No "works on my machine" issues because the MySQL version, Node version, and OS dependencies are pinned in Dockerfiles.

### Mock Seeding in Lifecycle

Seeding is not an afterthought but part of the container startup sequence. This decision means:
1. The system is always in a demonstrable state for stakeholders.
2. E2E tests are deterministic.
3. New developers are productive within minutes, not hours.

The idempotent upsert pattern means accidental double-seeds cause no harm.

### Trade-offs Accepted

| Decision | Trade-off |
|----------|-----------|
| HttpOnly cookies for JWT | Requires CORS configuration; slightly more complex than localStorage, but significantly more secure |
| Single monorepo | Simpler for a small team; would need Nx/Turborepo tooling if the codebase grows beyond ~10 modules |
| No Redis (no session/queue) | Refresh token revocation requires DB check; acceptable for internal tool, not acceptable for high-security systems |
| No message queue | Progress update events are synchronous; sufficient for 3–5 developers testing locally |
