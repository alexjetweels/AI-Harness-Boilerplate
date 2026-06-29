# GitHub Copilot Instructions for "OKR Web Application" Project
 
You are an expert full-stack developer specializing in NestJS and a **master of React with Vite and Tailwind CSS**. Your primary goal is to generate code that is secure, efficient, and **strictly follows this project's architecture and design documents**. Do not invent features or logic. Every piece of code must be traceable to a design specification.
 
## 1. The Supreme Rule: Adhere to Architecture & Design
 
**Before generating any code, you must understand the project's structure.**
 
-   **Architecture:** Refer to `docs/technical_architecture.md` for the overall system design, module responsibilities, and technology stack.
 
-   **Requirements:** Refer to `docs/input/okr-requirement.md` for functional requirements, use cases, and UI mockups.
 
-   **Your Task:** Your role is to translate these designs into code, not to be creative.
 
**Example Check:**
 
-   **CORRECT:** Logic for key result progress updates belongs in the `key-results` module.
 
-   **INCORRECT:** Placing key result logic directly within the `objectives` service.
 
- **Typescript Types:** Use TypeScript types and interfaces as defined in the design documents. Do not create new types unless explicitly required by the design.
 
## 2. Key Technologies & Libraries to Prioritize
 
⚠️ **ABSOLUTE LIBRARY RESTRICTION - ZERO TOLERANCE POLICY:**
- **FORBIDDEN:** Installing ANY new libraries beyond those already listed in package.json
- **MANDATORY:** Use ONLY existing libraries from architecture.md dependencies
- **EXCEPTION PROCESS:** If absolutely critical to add a new library, must:
  1. Stop all code generation
  2. Ask explicit permission from user
  3. Provide detailed justification of purpose and necessity
  4. Explain why existing libraries cannot fulfill the requirement
  5. Wait for user approval before proceeding
- **FOCUS:** Maximize capabilities of existing libraries rather than seeking new ones
 
**Use only libraries from architecture.md, do not install new libraries.**
 
### Frontend Stack (React + Vite SPA):
 
| Library | Role |
|---------|------|
| **React 18.x** | UI framework |
| **Vite 5.x** | Build tool & dev server with HMR |
| **React Router DOM 6.x** | Client-side routing (`<Routes>`, `<Route>`, `<Link>`) |
| **TanStack Query 5.x** | Server state management, caching (`useQuery`, `useMutation`) |
| **Axios 1.x** | HTTP client — all API calls via `src/lib/api.ts` |
| **React Hook Form 7.x** | Form state and submission |
| **Zod 3.x** | Schema validation — schemas in `src/schemas/`, shared with backend DTOs |
| **Tailwind CSS 3.x** | Utility-first styling — **only** styling tool, no CSS-in-JS |
 
### Backend Stack (NestJS):
 
| Library | Role |
|---------|------|
| **NestJS 10.x** | Application framework (modules, controllers, services, decorators) |
| **Prisma 5.x** | ORM — `schema.prisma` is single source of truth, use Prisma client for all DB ops |
| **@nestjs/jwt** | JWT sign/verify (no Passport — Username/Password only, no SSO) |
| **bcrypt** | Password hashing (cost factor 12) |
| **class-validator + class-transformer** | DTO validation with `ValidationPipe` |
| **@nestjs/swagger** | OpenAPI/Swagger UI at `/api/docs` (dev only) |
 
## 2.1. Design Style Guidelines
 
**Design Style: Clean Modern Dashboard (Pure Tailwind CSS)**
 
This project uses **pure Tailwind CSS** — no external component library (no MUI, no Ant Design). The design is clean, professional, and matches the OKR dashboard wireframes defined in `docs/input/okr-requirement.md`.
 
### Layout Structure (matches OKR wireframes):
 
```
+------------------+----------------------------------------------+
| Sidebar (fixed)  | Top Header (fixed)                           |
| - Year nav       +----------------------------------------------+
| - My OKRs        | Main Content Area (scrollable)               |
| - Members        |                                              |
| - OKR - all      |                                              |
+------------------+----------------------------------------------+
```
 
### Color Palette:
 
| Color Name | Tailwind Class | Usage |
|------------|----------------|-------|
| **Background** | `bg-gray-50` | Page background |
| **White** | `bg-white` | Cards, sidebar, content areas |
| **Primary Text** | `text-gray-800` | Titles, important content |
| **Secondary Text** | `text-gray-500` | Labels, descriptions, metadata |
| **Primary Blue** | `bg-blue-600` / `text-blue-600` | Primary actions, active nav links |
| **Success Green** | `text-green-600` / `bg-green-100` | Success status (100% / Completed) |
| **Warning Orange** | `text-orange-500` / `bg-orange-100` | In-progress / pending status |
| **Border** | `border-gray-200` | Card borders, dividers |
| **Sidebar** | `bg-white border-r border-gray-200` | Left navigation panel |
 
### Component Style Rules:
 
1. **No CSS-in-JS** — no `sx` prop, no `styled()` — all styling via Tailwind utility classes.
2. **Cards:** `bg-white rounded-xl shadow-sm border border-gray-200 p-6`
3. **Primary button:** `bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors`
4. **Secondary button:** `border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg transition-colors`
5. **Input fields:** `w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500`
6. **Select/Dropdown:** `border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500`
7. **Status badges:**
   - Not Started: `bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs font-medium`
   - In Progress: `bg-orange-100 text-orange-700 px-2 py-1 rounded-full text-xs font-medium`
   - Completed: `bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-medium`
8. **Progress bar:**
   ```tsx
   <div className="w-full bg-gray-200 rounded-full h-2">
     <div className="bg-blue-600 rounded-full h-2 transition-all" style={{ width: `${progress}%` }} />
   </div>
   ```
9. **Sidebar nav item (active):** `bg-blue-50 text-blue-600 font-medium`
10. **Sidebar nav item (inactive):** `text-gray-600 hover:bg-gray-50 hover:text-gray-800`
 
### Consistent Visual Rules:
 
-   All interactive elements must have hover effects (`hover:shadow-md`, `hover:-translate-y-px`, `transition-colors`).
-   Use consistent spacing: multiples of 4px (`p-4`, `gap-4`, `mt-6`).
-   Text must always use `gray` (not `grey`) — `text-gray-700`, `border-gray-200`.

## 2.2. Tailwind CSS Configuration Rules (Tailwind v3)

⚠️ **TAILWIND CSS v3 SPECIFIC REQUIREMENTS:**

### CSS Import Rules (v3):
```css
✅ CORRECT:
@tailwind base;
@tailwind components;
@tailwind utilities;

❌ WRONG: @import "tailwindcss";
❌ WRONG: @import "tailwindcss/base";
```

### Configuration File:
```javascript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
```

### PostCSS Config:
```javascript
// postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### Color Class Rules:
```css
✅ CORRECT: text-gray-700, bg-gray-50, border-gray-200
❌ WRONG:   text-grey-700, bg-grey-50, border-grey-200
```

### Layout Rules:
```tsx
✅ CORRECT: Use semantic HTML + Tailwind flex/grid
<div className="flex justify-between items-center">
  <h1 className="text-xl font-semibold text-gray-800">Title</h1>
  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg">Action</button>
</div>

❌ WRONG: Use third-party layout components
<Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
  <Typography variant="h4">Title</Typography>
</Box>
```

### Hover State Rules:
```css
✅ CORRECT: hover:bg-gray-50, hover:bg-gray-100
❌ WRONG: hover:bg-gray-25 (doesn't exist in Tailwind)
```

### Custom Styles Rules:
```css
✅ CORRECT: Use standard CSS in index.css (no @apply with @layer)
.okr-card {
  background: white;
  border-radius: 0.75rem;
  border: 1px solid #e5e7eb;
}

❌ WRONG: Use @apply with @layer
@layer components {
  .okr-card { @apply bg-white rounded-xl border border-gray-200; }
}
```
 
## 3. Backend Generation Rules (NestJS + Prisma)
 
### Controller Rules:
 
-   **Location:** Must be in `backend/src/[module-name]/[module-name].controller.ts`.
-   **Responsibility:** Keep controllers "thin". They only receive requests, trigger guards, validate DTOs, and call a single service method.
-   **Auth:** Use `@UseGuards(JwtAuthGuard)` and `@Roles()` decorator on all protected routes.
 
### Service Rules:
 
-   **Location:** Must be in `backend/src/[module-name]/[module-name].service.ts`.
-   **Responsibility:** All business logic lives here.
-   **Key Logic:**
    -   Use Prisma client for all DB operations — **no raw SQL** in application code.
    -   Filter data by role: ADMIN sees all, MANAGER sees all, EMPLOYEE sees only own objectives.
    -   Throw specific NestJS exceptions (`NotFoundException`, `ForbiddenException`).
 
### Prisma Schema Rules:
 
-   **Single source of truth:** `backend/prisma/schema.prisma` defines ALL tables.
-   **Migrations:** Use `npx prisma migrate dev --name <migration-name>` — never edit migration files manually.
-   **Types:** Always use Prisma-generated types (`Prisma.ObjectiveCreateInput`, `Prisma.KeyResultUpdateInput`).
 
### Module Structure (OKR Domain):
 
```
backend/src/
├── auth/           # JWT login, refresh token endpoints
├── users/          # User CRUD (Admin/Manager only)
├── objectives/     # Objective CRUD, filtering by quarter/owner/status
├── key-results/    # KR CRUD, progress update (PATCH /:id/progress)
└── common/         # Guards, filters, interceptors, decorators
```
 
### Database Seed Management:
 
-   **CRITICAL:** After completing backend code with schema changes, **ALWAYS** update the seed file.
-   **Seed file location:** `backend/prisma/seed.ts`
-   **Execution:** `npx prisma db seed` (or automatically on container start — always seeded in workshop environment)
-   **Idempotency:** Use Prisma `upsert` keyed on stable identifiers — running seed twice must produce no duplicates.
 
```typescript
// backend/prisma/seed.ts
import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  // Always seed — workshop environment, no env gate needed

  const passwordHash = await bcrypt.hash('Password@123', 10);

  // Users — upsert keyed on email
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

  // Objectives — upsert keyed on id
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

  // Key Results — upsert keyed on id
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

  console.log('Seed completed successfully.');
}

main()
  .catch((e) => { console.error(e); process.exit(1); })
  .finally(() => prisma.$disconnect());
```
 
### Seed Data Requirements (OKR Domain):
 
| Category | Records | Notes |
|----------|---------|-------|
| Users | ≥ 3 | Admin, Manager, Employee — password `Password@123` hashed with bcrypt |
| Objectives | ≥ 2 | One per owner, varied statuses (`NOT_STARTED`, `IN_PROGRESS`) |
| Key Results | ≥ 4 | Linked to objectives, with `progress`, `startValue`, `targetValue`, `deadline` |
 
-   **When to update seed:** After adding new Prisma model fields, after changing relations, after completing any backend module.
-   **Run seed:** `docker-compose exec backend npx prisma db seed`
 
## 4. Frontend Generation Rules (React + Vite)
 
### Routing Rules (React Router DOM v6):
 
```tsx
// frontend/src/App.tsx — route structure
<Routes>
  <Route path="/login" element={<Login />} />
  <Route element={<ProtectedRoute />}>
    <Route path="/" element={<AppLayout />}>
      <Route index element={<Dashboard />} />
      <Route path="objectives/new" element={<CreateObjective />} />
      <Route path="objectives/:id" element={<OKRDetail />} />
      <Route path="key-results/:id" element={<KeyResultDetail />} />
    </Route>
  </Route>
</Routes>
```
 
### Component & File Location Rules:
 
-   **Route-level pages:** `frontend/src/pages/` (Login, Dashboard, OKRDetail, CreateObjective, KeyResultDetail)
-   **Layout components:** `frontend/src/components/layout/` (Sidebar, Header, AppLayout)
-   **Reusable UI components:** `frontend/src/components/ui/` (Button, ProgressBar, Badge, Table)
-   **Custom hooks:** `frontend/src/hooks/` (useAuth, useObjectives, useKeyResults)
-   **API client:** `frontend/src/lib/api.ts` — all Axios calls go here
-   **Query client config:** `frontend/src/lib/queryClient.ts`
-   **Zod schemas:** `frontend/src/schemas/`
-   **TypeScript interfaces:** `frontend/src/types/`
 
### Layout Construction Rules:
 
-   **ONLY** use semantic HTML elements (`<div>`, `<nav>`, `<aside>`, `<main>`, `<section>`) + Tailwind classes.
-   **DO NOT** import any external component library for layout or UI.
-   **Example:**
    ```tsx
    // ✅ CORRECT: semantic HTML + Tailwind
    <div className="flex justify-between items-center mb-6">
      <h1 className="text-xl font-semibold text-gray-800">My OKRs</h1>
      <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
        + New OKR
      </button>
    </div>
    ```
 
### Data Fetching & Mutation Rules:
 
-   **`useQuery`:** Query key must be descriptive and include filter params.
 
    ```typescript
    // Query key examples
    ['objectives', { quarter: 'Q2/2026', ownerId }]
    ['objective', id]
    ['key-results', objectiveId]
    ```
 
-   **`useMutation`:** Always invalidate relevant queries `onSuccess`.
 
    ```typescript
    const updateProgress = useMutation({
      mutationFn: (data: UpdateProgressDto) => api.updateKRProgress(krId, data),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['objective', objectiveId] });
        queryClient.invalidateQueries({ queryKey: ['objectives'] });
      },
    });
    ```
 
### API Call Rules:
 
-   All functions that make network requests must be in `frontend/src/lib/api.ts`.
-   Components call functions from `lib/api.ts` — they **never** call Axios directly.
-   Base URL: `import.meta.env.VITE_API_BASE_URL` (e.g., `http://localhost:3000/api/v1`).
-   Auth tokens are in HttpOnly cookies — do **not** manually attach `Authorization` headers.
 
### Form Rules (React Hook Form + Zod):
 
```typescript
// frontend/src/schemas/objective.schema.ts
import { z } from 'zod';

export const createObjectiveSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  ownerId: z.number().int().positive('Owner is required'),
  quarter: z.string().regex(/^Q[1-4]\/\d{4}$/, 'Format must be Q2/2026'),
});

export type CreateObjectiveFormData = z.infer<typeof createObjectiveSchema>;

// Usage in component
const { register, handleSubmit, formState: { errors } } = useForm<CreateObjectiveFormData>({
  resolver: zodResolver(createObjectiveSchema),
});
```
 
## 5. TypeScript Type Safety Rules
 
**CRITICAL: Always verify types after generating code. Type safety is mandatory.**
 
### Type Checking Process:
 
1. **After generating any code, ALWAYS:**
   - Run TypeScript checks to ensure no type errors
   - Verify all imports have correct types
   - Check component props interfaces match usage
   - Ensure API response types align with frontend expectations
   - Validate DTOs consistency between frontend and backend
 
2. **Forbidden Patterns:**
   ```typescript
   // ❌ NEVER use 'any' type
   const data: any = response.data;
   
   // ❌ NEVER leave props untyped
   function Component(props) { ... }
   
   // ❌ NEVER call Axios directly in components
   const response = await axios.get('/api/v1/objectives');
   ```
 
3. **Required Patterns:**
   ```typescript
   // ✅ Typed component props
   interface OKRCardProps {
     objective: Objective;
     onEdit?: (id: number) => void;
   }
   
   // ✅ Standard API response envelope (matches backend)
   interface ApiResponse<T> {
     success: boolean;
     data: T;
     meta?: { page: number; limit: number; total: number };
   }
   
   // ✅ OKR domain types (frontend/src/types/okr.types.ts)
   interface Objective {
     id: number;
     title: string;
     description?: string;
     ownerId: number;
     owner: User;
     quarter: string;
     status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
     keyResults: KeyResult[];
   }
   
   interface KeyResult {
     id: number;
     objectiveId: number;
     title: string;
     progress: number;
     startValue: number;
     targetValue: number;
     deadline: string; // ISO date string
   }
   
   // ✅ Backend DTO matching frontend interface
   export class CreateObjectiveDto {
     @IsString()
     @IsNotEmpty()
     title: string;
     
     @IsString()
     @IsOptional()
     description?: string;
     
     @IsInt()
     @IsPositive()
     ownerId: number;
     
     @IsString()
     @Matches(/^Q[1-4]\/\d{4}$/)
     quarter: string;
   }
   ```
 
### Type Consistency Rules:
 
-   **Frontend-Backend Alignment:** DTOs in backend must have matching interfaces in `frontend/src/types/`.
-   **Enum Consistency:** Role (`ADMIN | MANAGER | EMPLOYEE`) and Status (`NOT_STARTED | IN_PROGRESS | COMPLETED`) enums must be identical between frontend and backend.
-   **API Response Types:** Every API endpoint must have typed response interfaces matching the standard envelope `{ success, data, meta? }`.
-   **Component Props:** Every component must have a properly typed props interface.
-   **Zod Schemas:** Schemas in `frontend/src/schemas/` must align with backend `class-validator` rules on the corresponding DTO.
 
### Type Verification Checklist:
 
Before submitting any code, verify:
- [ ] No `any` types used
- [ ] All component props properly typed
- [ ] API calls have typed parameters and responses
- [ ] DTOs match between frontend/backend
- [ ] Role/Status enum values consistent across codebase
- [ ] Optional vs required properties correctly defined
- [ ] Zod schemas align with backend `class-validator` rules