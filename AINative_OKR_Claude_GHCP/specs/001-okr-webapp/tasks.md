# Task List: OKR Web Application Implementation

**Feature**: OKR Web Application  
**Feature ID**: 001-okr-webapp  
**Module ID**: mod00  
**Created**: 2026-07-02  
**Language**: Vietnamese  
**Total Effort**: 106 story points  
**Implementation Phases**: 5  

---

## Executive Summary

Danh sách công việc toàn diện cho dự án "OKR Web Application" - một hệ thống quản lý OKR (Objectives & Key Results) full-stack với quy trình phê duyệt đa giai đoạn và kiểm soát truy cập dựa trên vai trò.

**Tổng quan**:
- **13 công việc** được chia thành **5 pha thực hiện**
- **106 điểm dự báo** tổng cộng
- **Đường dẫn quan trọng**: T-001 → T-002 → T-003 → T-005 → T-006 → T-007 → T-008 → T-009 (79 pts)
- **Khoảng thời gian dự kiến**: 3-4 tuần với nhóm 2-3 người phát triển

**Quy tắc chất lượng bắt buộc**:
- Tất cả công việc tuân theo TDD (Test-Driven Development) - test được viết trước khi code
- Cần thiết có unit test ≥70%, integration test 100% cho các luồng quan trọng
- Mỗi hoàn thành công việc phải cập nhật dữ liệu seed
- Code review bắt buộc trước khi merge

---

## Pha Thực Hiện

### Pha 1: Auth & Core Backend (21 pts)
**T-001, T-002** - Nền tảng xác thực JWT, refresh token, session management

### Pha 2: Dashboard & OKR CRUD (21 pts)
**T-003, T-005, T-006** - Giao diện dashboard, form tạo Objective, backend CRUD

### Pha 3: KR & Submit (18 pts)
**T-007, T-008** - CRUD Key Result, luồng submit, khóa cấu trúc post-submit

### Pha 4: Manager Views & Approval (26 pts)
**T-004, T-009, T-011** - Dashboard manager, phê duyệt/từ chối, trang Members

### Pha 5: Detail & Progress Tracking (23 pts)
**T-010, T-012, T-013** - Trang chi tiết OKR, cập nhật tiến độ, Grade & Feedback

---

## Danh Sách Chi Tiết Công Việc

---

### T-001: Xác Thực & Bảo Vệ Phiên (Auth Login & Session Protection)

**User Story Link**: US-1 (Scenarios 1-7)  
**Pha**: 1 (Auth & Core Backend)  
**Story Points**: 13  
**Priority**: P1  
**Trạng thái**: Chưa bắt đầu  

#### Tiêu Chí Chấp Nhận

1. ✅ GET request đến route được bảo vệ mà không có token → redirect về `/login`
2. ✅ POST `/api/v1/auth/login` với email/password hợp lệ → trả về Access Token + Refresh Token trong HttpOnly cookie
3. ✅ POST `/api/v1/auth/login` với email không tồn tại hoặc password sai → HTTP 400 với thông báo lỗi chung (không phân biệt loại)
4. ✅ Access Token có TTL 1h; Refresh Token có TTL 7d
5. ✅ Cookies đặt HttpOnly và SameSite=Strict
6. ✅ Rate limiting: >60 requests/phút từ cùng IP → HTTP 429
7. ✅ Logout xóa cookies và redirect về `/login`; nút back không khôi phục session

#### Chi Tiết Thực Hiện

**Backend Architecture**:
- NestJS auth module với JwtService
- Bcrypt password validation (cost factor 12)
- HttpOnly cookie setup via `res.cookie()` với SameSite=Strict
- Rate limiting middleware using @nestjs/throttler

**Frontend Architecture**:
- `ProtectedRoute` component bọc tất cả protected path
- `useAuth` hook quản lý token state
- Axios interceptor cho auto-refresh trên 401

**Database**:
- Prisma User model: id, email (unique), name, password (hashed), role (ADMIN|MANAGER|EMPLOYEE), createdAt, updatedAt
- Seed 3 users: admin@okr.local, manager@okr.local, employee@okr.local với password đã hash

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ bcrypt hash validation (password đúng/sai)
- ✅ JWT token generation (correct payload)
- ✅ Rate limiter counter logic

**Integration Tests**:
- ✅ POST /auth/login với credentials hợp lệ → check response shape (access_token, refresh_token, expires_in)
- ✅ POST /auth/login invalid credentials → verify 400 + generic error message (no email enumeration)
- ✅ Set-Cookie headers có HttpOnly, SameSite=Strict attributes
- ✅ Rate limiting — gửi 61 requests/phút, xác minh yêu cầu 60 thành công, yêu cầu 61 trả về 429
- ✅ POST /auth/logout → cookies xóa, 200 OK

**E2E Tests**:
- ✅ Unauthenticated user tries GET / → redirects to /login
- ✅ Login → verify session token in cookie exists (can't read value, but verify it exists)
- ✅ Click logout → cookies deleted
- ✅ Navigate back after logout → stays on /login (no session restored)

#### Files to Create/Modify

**Backend**:
- `backend/src/auth/auth.controller.ts` (Login, logout endpoints)
- `backend/src/auth/auth.service.ts` (Token issuance, bcrypt verification)
- `backend/src/auth/auth.module.ts` (Module definition)
- `backend/src/auth/dto/login.dto.ts` (LoginDto with email, password)
- `backend/src/common/guards/jwt-auth.guard.ts` (Extract + validate JWT from cookie)
- `backend/src/common/decorators/roles.decorator.ts` (Role-based guards)
- `backend/src/common/middleware/rate-limit.middleware.ts` (Throttler config)
- `backend/src/common/strategies/jwt.strategy.ts` (JWT validation strategy)

**Frontend**:
- `frontend/src/components/layout/ProtectedRoute.tsx` (Route guard with redirect)
- `frontend/src/hooks/useAuth.ts` (Auth state hook)
- `frontend/src/lib/api.ts` (Axios instance + interceptor setup)
- `frontend/src/pages/Login.tsx` (Login form)
- `frontend/src/types/auth.types.ts` (Auth TypeScript interfaces)
- `frontend/src/schemas/auth.schema.ts` (Zod validation for login)

**Database**:
- `backend/prisma/schema.prisma` (User model definition)
- `backend/prisma/seed.ts` (Seed 3 test users)
- `backend/prisma/migrations/001_init_users.sql` (Auto-generated)

#### Dependencies

- None (first task in sequence)

#### Definition of Done

- [ ] Tất cả test trước khi implementation
- [ ] Unit tests pass ≥5 test cases
- [ ] Integration tests pass ≥7 test cases
- [ ] E2E tests pass ≥4 test cases
- [ ] Code review pass
- [ ] Seed data updated
- [ ] TypeScript types checked (no `any` type)
- [ ] Postman/API client có thể test endpoints
- [ ] Rate limiting hoạt động (manual test với curl loop)

---

### T-002: Token Refresh & Auto-Renewal (Auth Refresh Flow)

**User Story Link**: US-1 (Scenarios 4-5)  
**Pha**: 1 (Auth & Core Backend)  
**Story Points**: 8  
**Priority**: P1  
**Dependency**: T-001-AUTH-LOGIN  

#### Tiêu Chí Chấp Nhận

1. ✅ Access Token hết hạn khi user hoạt động (trong test: TTL 5 giây)
2. ✅ Frontend nhận 401 trên API call bất kỳ
3. ✅ Frontend tự động gọi POST `/api/v1/auth/refresh`
4. ✅ Backend validate Refresh Token, phát hành Access Token mới
5. ✅ Frontend retry request ban đầu với token mới
6. ✅ User không thấy gián đoạn (transparent refresh)
7. ✅ Nếu cả Access Token và Refresh Token đều hết hạn → redirect `/login` với thông báo timeout

#### Chi Tiết Thực Hiện

**Backend**:
- POST `/api/v1/auth/refresh` endpoint không cần JwtAuthGuard (dùng middleware để extract refresh token)
- Validate Refresh Token signature + expiry
- Issue new Access Token (1h TTL)
- Return 401 nếu refresh token hết hạn/không hợp lệ

**Frontend**:
- Axios interceptor với retry logic trên 401
- Queue pending requests khi refresh đang trong flight (tránh race condition)
- Handle final 401 → redirect `/login` với toast "Phiên làm việc đã hết hạn"

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ JWT token expiry detection (check `exp` claim)
- ✅ Token decode without validation (extract subject)

**Integration Tests**:
- ✅ POST /auth/refresh với valid refresh token → returns new access token (verify token shape)
- ✅ POST /auth/refresh với expired refresh token → returns 401
- ✅ POST /auth/refresh với missing token → returns 401
- ✅ Access token from refresh has correct TTL (1h = 3600 seconds)

**E2E Tests**:
- ✅ Axios interceptor on 401 → calls refresh endpoint → retries original request (network spy verify 2 calls)
- ✅ Both tokens expired → redirect to /login with timeout message visible
- ✅ Create objective → pause 1h (simulate access token expiry) → update progress → no interruption (auto-refresh + retry)

#### Files to Create/Modify

**Backend**:
- `backend/src/auth/auth.controller.ts` (add POST /refresh endpoint)
- `backend/src/auth/auth.service.ts` (add refreshAccessToken method)

**Frontend**:
- `frontend/src/lib/api.ts` (enhance interceptor with retry + queue logic)
- `frontend/src/hooks/useAuth.ts` (add handleTokenExpiry)

#### Dependencies

- T-001-AUTH-LOGIN

#### Definition of Done

- [ ] Token refresh endpoint tested ≥3 scenarios
- [ ] Axios interceptor tested with E2E
- [ ] Queue logic handles race condition (multiple 401s simultaneously)
- [ ] Session timeout message displays to user
- [ ] Code review pass

---

### T-003: Employee Dashboard View (Role-Based OKR List)

**User Story Link**: US-2 (Scenarios 1-3, 6-7)  
**Pha**: 2 (Dashboard & OKR CRUD)  
**Story Points**: 8  
**Priority**: P1  
**Dependency**: T-001-AUTH-LOGIN  

#### Tiêu Chí Chấp Nhận

1. ✅ EMPLOYEE đăng nhập → Dashboard hiển thị
2. ✅ Dashboard chỉ hiển thị OKR được sở hữu bởi EMPLOYEE (bao gồm draft)
3. ✅ Sidebar hiển thị chỉ "My OKRs" (không "Members", không "OKR-all")
4. ✅ Link "Members" KHÔNG render trong DOM (không chỉ ẩn bằng opacity)
5. ✅ Empty state: "Chưa có OKR nào. Nhấn NEW OKR để tạo mới."
6. ✅ Quarter filter dropdown: chọn Q2/2026 → danh sách cập nhật
7. ✅ Không có OKR từ user khác hiển thị

#### Chi Tiết Thực Hiện

**Backend**:
- `objectives.service.ts` method `findAllForEmployee(userId, quarter?)` filters by ownerId + quarter
- GET `/api/v1/objectives` với auth EMPLOYEE → query tự động filter ownerId

**Frontend**:
- `Dashboard.tsx` component hiển thị OKR list từ query
- `Sidebar.tsx` conditional rendering nav items dựa trên role
- Quarter filter component

**Database**:
- Seed OKR data cho test EMPLOYEE

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ Filter OKR list by ownerId and quarter (backend service logic)

**Integration Tests**:
- ✅ GET /api/v1/objectives (EMPLOYEE auth) → returns only own OKR
- ✅ GET /api/v1/objectives?quarter=Q2/2026 (EMPLOYEE) → filters by quarter
- ✅ Response không bao gồm draft OKR của manager

**E2E Tests**:
- ✅ Login as EMPLOYEE → Dashboard loads → sidebar has no "Members" link (inspect DOM)
- ✅ Create multiple OKR with different quarters → verify filter works
- ✅ Empty dashboard (delete all OKR) → shows empty state message

#### Files to Create/Modify

**Backend**:
- `backend/src/objectives/objectives.service.ts` (add findAllForEmployee method)
- `backend/src/objectives/objectives.controller.ts` (GET /objectives with filtering)
- `backend/src/objectives/dto/get-objectives.dto.ts` (Query params DTO)

**Frontend**:
- `frontend/src/pages/Dashboard.tsx` (OKR list display + filters)
- `frontend/src/components/layout/Sidebar.tsx` (role-conditional rendering)
- `frontend/src/hooks/useObjectives.ts` (custom hook for fetching OKRs)
- `frontend/src/types/okr.types.ts` (Objective TypeScript interface)
- `frontend/src/schemas/objective.schema.ts` (Zod validation)

**Database**:
- `backend/prisma/seed.ts` (add sample OKR for EMPLOYEE)

#### Dependencies

- T-001-AUTH-LOGIN

#### Definition of Done

- [ ] Backend filtering logic tested
- [ ] Frontend displays only own OKR
- [ ] Sidebar DOM inspection: no "Members" element
- [ ] Quarter filter functional
- [ ] Empty state message displays
- [ ] Code review pass

---

### T-004: Manager Dashboard View (Managed & Personal OKR Tabs)

**User Story Link**: US-2 (Scenarios 4-5)  
**Pha**: 4 (Manager Views & Approval)  
**Story Points**: 8  
**Priority**: P1  
**Dependency**: T-003-DASHBOARD-EMPLOYEE-VIEW  

#### Tiêu Chí Chấp Nhận

1. ✅ MANAGER đăng nhập → Dashboard hiển thị
2. ✅ Sidebar hiển thị 4 nav item: "I created", "I manage", "Members", "OKR-all"
3. ✅ "I created" tab: OKR được sở hữu bởi MANAGER (giống EMPLOYEE view cho user)
4. ✅ "I manage" tab: OKR sở hữu bởi EMPLOYEE với isSubmitted=true chỉ (loại exclude draft + MANAGER OKR)
5. ✅ MANAGER truy cập `/members` qua URL → backend 403 hoặc redirect
6. ✅ GET `/api/v1/members` (EMPLOYEE auth) → 403
7. ✅ GET `/api/v1/members` (MANAGER auth) → danh sách Personal EMPLOYEE OKR

#### Chi Tiết Thực Hiện

**Backend**:
- `objectives.service.ts` adds `findManagedOKR(managerId, quarter?)` filtering `ownerId != managerId` + `isSubmitted = true` + `type = PERSONAL`
- GET `/api/v1/members` endpoint với `@UseGuards(JwtAuthGuard)` + `@Roles('MANAGER', 'ADMIN')`

**Frontend**:
- Dashboard tabs component switching between "I created" (query owned) and "I manage" (query managed)
- Members.tsx as separate route under sidebar navigation

#### Công Việc Test (TDD)

**Integration Tests**:
- ✅ GET /api/v1/objectives (MANAGER auth) → returns own OKR + submitted employee OKR
- ✅ GET /api/v1/objectives?type=managed (MANAGER auth) → returns only submitted EMPLOYEE OKR (not MANAGER)
- ✅ GET /api/v1/members (EMPLOYEE auth) → 403
- ✅ GET /api/v1/members (MANAGER auth) → returns Personal submitted EMPLOYEE OKR only
- ✅ GET /api/v1/members?quarter=Q2/2026 (MANAGER) → filtered by quarter

**E2E Tests**:
- ✅ Login as MANAGER → Dashboard loads
- ✅ Sidebar shows 4 nav items (I created, I manage, Members, OKR-all)
- ✅ "I manage" tab populated with submitted EMPLOYEE OKR (not MANAGER own drafts)
- ✅ EMPLOYEE user tries accessing /members → backend 403 or redirect

#### Files to Create/Modify

**Backend**:
- `backend/src/objectives/objectives.service.ts` (add findManagedOKR method)
- `backend/src/objectives/objectives.controller.ts` (add GET /members endpoint)

**Frontend**:
- `frontend/src/pages/Dashboard.tsx` (add tabs "I created" vs "I manage")
- `frontend/src/pages/Members.tsx` (new page)
- `frontend/src/components/layout/Sidebar.tsx` (update nav items for MANAGER)
- Update routing in `frontend/src/App.tsx`

**Database**:
- `backend/prisma/seed.ts` (add MANAGER + multiple EMPLOYEE OKR mix: draft + submitted)

#### Dependencies

- T-003-DASHBOARD-EMPLOYEE-VIEW

#### Definition of Done

- [ ] "I manage" query tested
- [ ] Members endpoint tested
- [ ] Members page renders correctly
- [ ] Tab switching functional
- [ ] Access control enforced (403 for EMPLOYEE)
- [ ] Code review pass

---

### T-005: Create Objective Form (Frontend Validation & Role-Based Type Field)

**User Story Link**: US-3 (Scenarios 1-6)  
**Pha**: 2 (Dashboard & OKR CRUD)  
**Story Points**: 5  
**Priority**: P1  
**Dependency**: T-001-AUTH-LOGIN  

#### Tiêu Chí Chấp Nhận

1. ✅ EMPLOYEE form shows: Title, Description, Type (dropdown với "Personal" chỉ), Quarter
2. ✅ MANAGER form shows: Title, Description, Type (dropdown với "Personal" + "Team"), Quarter
3. ✅ No Owner field visible (auto-assigned from JWT)
4. ✅ Title required (validation error nếu rỗng)
5. ✅ Description optional
6. ✅ Quarter format validation: Q[1-4]/YYYY (e.g., Q2/2026)
7. ✅ Type field reflects role restriction (EMPLOYEE không thể chọn "Team")

#### Chi Tiết Thực Hiện

**Frontend Only** (no backend logic yet):
- React Hook Form + Zod schema
- Type dropdown conditionally populated based on role from useAuth hook
- Real-time validation errors

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ Zod schema validation for CreateObjectiveDto (title required, quarter format regex)
- ✅ Type enum validation (PERSONAL or TEAM)

**E2E Tests**:
- ✅ EMPLOYEE form loads → Type dropdown shows "Personal" only
- ✅ MANAGER form loads → Type dropdown shows "Personal" and "Team"
- ✅ Submit with invalid quarter format → displays validation error
- ✅ Submit with empty title → displays "Tiêu đề không được trống"
- ✅ Form fields populate from state correctly

#### Files to Create/Modify

**Frontend**:
- `frontend/src/pages/CreateObjective.tsx` (main form page)
- `frontend/src/schemas/objective.schema.ts` (Zod validation)
- `frontend/src/components/form/ObjectiveForm.tsx` (reusable form component)
- `frontend/src/types/okr.types.ts` (TypeScript interfaces)

#### Dependencies

- T-001-AUTH-LOGIN (auth required để lấy role)

#### Definition of Done

- [ ] Zod schema matches spec
- [ ] Type dropdown logic correct for both roles
- [ ] Validation errors display correctly
- [ ] Form submittable (placeholder handler)
- [ ] Code review pass
- [ ] No TypeScript errors

---

### T-006: Create Objective Backend (Auto-Owner Assignment & Type Enforcement)

**User Story Link**: US-3 (Scenarios 3-4)  
**Pha**: 2 (Dashboard & OKR CRUD)  
**Story Points**: 8  
**Priority**: P1  
**Dependency**: T-005-CREATE-OBJECTIVE-FORM  

#### Tiêu Chí Chấp Nhận

1. ✅ POST `/api/v1/objectives` accepts: title, description, type, quarter
2. ✅ Backend auto-assigns ownerId from JWT token
3. ✅ New Objective created với isSubmitted=false, approvalStatus=PENDING
4. ✅ EMPLOYEE sending type=TEAM → HTTP 403 Forbidden (backend enforces)
5. ✅ Invalid quarter format → 400
6. ✅ Empty title → 400
7. ✅ Created Objective returned trong response với id, all fields
8. ✅ Chỉ owner thấy draft (subsequent dashboard queries filter by ownerId)

#### Chi Tiết Thực Hiện

**Backend**:
- POST endpoint với JwtAuthGuard
- Extract userId from request.user
- Validate type vs role trong service (throw 403 nếu EMPLOYEE + type=TEAM)
- Prisma create with isSubmitted=false, approvalStatus=PENDING

**Database**:
- Prisma Objective model: id, title, description, type (ENUM), ownerId (FK), quarter, isSubmitted (BOOLEAN), approvalStatus (ENUM), grade (nullable), createdAt, updatedAt

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ CreateObjectiveDto validation (class-validator)
- ✅ Type enum validation
- ✅ Quarter regex validation

**Integration Tests**:
- ✅ POST /api/v1/objectives với EMPLOYEE + type=TEAM → 403
- ✅ POST /api/v1/objectives với valid data → 201 + new objective returned
- ✅ Verify ownerId trong response matches JWT subject
- ✅ Verify isSubmitted=false + approvalStatus=PENDING
- ✅ POST với invalid quarter → 400
- ✅ POST với empty title → 400
- ✅ GET /api/v1/objectives (as EMPLOYEE) → see only own draft
- ✅ GET /api/v1/objectives (as MANAGER) → drafted EMPLOYEE OKR NOT visible

**E2E Tests**:
- ✅ Fill form → create objective → verify in dashboard

#### Files to Create/Modify

**Backend**:
- `backend/src/objectives/objectives.controller.ts` (POST /objectives)
- `backend/src/objectives/objectives.service.ts` (createObjective method)
- `backend/src/objectives/dto/create-objective.dto.ts` (with class-validator)
- `backend/src/app.module.ts` (register ObjectiveModule)

**Database**:
- `backend/prisma/schema.prisma` (add Objective model)
- `backend/prisma/migrations/002_create_objectives.sql` (auto-generated)
- `backend/prisma/seed.ts` (add sample objectives)

#### Dependencies

- T-005-CREATE-OBJECTIVE-FORM

#### Definition of Done

- [ ] Backend endpoint tested
- [ ] Type enforcement working (403 for EMPLOYEE+TEAM)
- [ ] Draft visibility correct
- [ ] Seed data updated
- [ ] Integration tests ≥6 cases
- [ ] Code review pass

---

### T-007: Key Results CRUD (Create, Update, Delete with Max 3 Limit)

**User Story Link**: US-4 (Scenarios 1-2)  
**Pha**: 3 (KR & Submit)  
**Story Points**: 10  
**Priority**: P1  
**Dependency**: T-006-CREATE-OBJECTIVE-BACKEND  

#### Tiêu Chí Chấp Nhận

1. ✅ GET `/api/v1/objectives/:id/key-results` returns KR list
2. ✅ POST `/api/v1/objectives/:id/key-results` creates KR (title, startValue, targetValue, deadline)
3. ✅ System enforces max 3 KR per Objective (400 if 4th attempt)
4. ✅ PATCH `/api/v1/key-results/:id` updates KR (title, startValue, targetValue, deadline)
5. ✅ DELETE `/api/v1/key-results/:id` removes KR
6. ✅ All mutations return 403 nếu objective isSubmitted=true (post-submit lock)
7. ✅ Frontend hides "Add KR" button khi count=3; shows "Đã đạt giới hạn 3 Key Results"

#### Chi Tiết Thực Hiện

**Backend**:
- KeyResult model linked to Objective via objectiveId FK
- Service validates count (≤3) + isSubmitted state
- Throws 403 on structure mutations post-submit
- GET, POST, PATCH, DELETE endpoints

**Frontend**:
- KR list component in OKR Detail page
- Form to add/edit/delete KR
- Add button disabled/hidden when count=3

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ KR validation (title required, startValue ≥ 0, targetValue > 0)
- ✅ Count enforcement logic

**Integration Tests**:
- ✅ POST /key-results on objective with 2 KR → succeeds (count=3)
- ✅ POST /key-results on objective with 3 KR → 400 "Max 3 KR"
- ✅ DELETE /key-results/:id → KR removed, count decreases
- ✅ POST /key-results on isSubmitted=true objective → 403
- ✅ PATCH /key-results/:id (title) on isSubmitted=true → 403
- ✅ GET /key-results for non-existent objective → 404

**E2E Tests**:
- ✅ Create KR 1, 2, 3 → add button becomes disabled
- ✅ Delete KR → add button re-enabled
- ✅ Edit KR title → changes persist

#### Files to Create/Modify

**Backend**:
- `backend/src/key-results/key-results.controller.ts` (CRUD endpoints)
- `backend/src/key-results/key-results.service.ts` (business logic)
- `backend/src/key-results/dto/create-key-result.dto.ts`
- `backend/src/key-results/dto/update-key-result.dto.ts`
- `backend/src/app.module.ts` (register KeyResultModule)

**Frontend**:
- `frontend/src/pages/ObjectiveDetail.tsx` (KR list display)
- `frontend/src/components/form/KeyResultForm.tsx` (add/edit form)
- `frontend/src/components/KeyResultList.tsx`
- `frontend/src/schemas/key-result.schema.ts` (Zod validation)
- `frontend/src/hooks/useKeyResults.ts`

**Database**:
- `backend/prisma/schema.prisma` (add KeyResult model)
- `backend/prisma/migrations/003_create_key_results.sql`
- `backend/prisma/seed.ts` (add sample KRs)

#### Dependencies

- T-006-CREATE-OBJECTIVE-BACKEND

#### Definition of Done

- [ ] CRUD operations tested (≥6 integration tests)
- [ ] Max 3 KR enforcement working
- [ ] Post-submit lock enforced (403)
- [ ] Frontend UI disabled/hidden correctly
- [ ] Seed data updated
- [ ] Code review pass

---

### T-008: Submit OKR Flow (State Transition & Visibility Change)

**User Story Link**: US-4 (Scenarios 3-8)  
**Pha**: 3 (KR & Submit)  
**Story Points**: 8  
**Priority**: P1  
**Dependency**: T-007-KEY-RESULTS-CRUD  

#### Tiêu Chí Chấp Nhận

1. ✅ Submit button disabled nếu Objective có 0 KR (tooltip: "Cần ít nhất 1 KR để submit")
2. ✅ Submit button enabled nếu ≥1 KR
3. ✅ Click Submit → confirmation dialog: "Sau khi submit, bạn không thể chỉnh sửa KR. Tiếp tục?"
4. ✅ Xác nhận gọi POST `/api/v1/objectives/:id/submit`
5. ✅ Backend sets isSubmitted=true, approvalStatus=PENDING
6. ✅ OKR appears in MANAGER "I manage" list
7. ✅ All edits to Title/Description/KR structure rejected với 403
8. ✅ Only owner sees draft; after submit, MANAGER can see per role rules

#### Chi Tiết Thực Hiện

**Backend**:
- POST endpoint `/objectives/:id/submit`
- Validate ≥1 KR (return 400 if 0)
- Atomic transaction: set isSubmitted=true, approvalStatus=PENDING
- Idempotent: calling twice returns 200 both times (no state change on 2nd call)

**Frontend**:
- Submit button logic (disabled < 1 KR)
- Confirmation dialog component
- Toast on success

#### Công Việc Test (TDD)

**Integration Tests**:
- ✅ POST /objectives/:id/submit on objective with 0 KR → 400
- ✅ POST /objectives/:id/submit with 1+ KR → 200, isSubmitted=true, approvalStatus=PENDING
- ✅ POST /objectives/:id/submit twice on same objective → idempotent (200, no double state change)
- ✅ After submit, PATCH /objectives/:id (title) → 403
- ✅ After submit, POST /objectives/:id/key-results → 403
- ✅ After submit, GET /objectives (MANAGER) → drafted OKR NOT visible; submitted visible in "I manage"

**E2E Tests**:
- ✅ Fill form → add 1 KR → Submit button becomes enabled
- ✅ Click Submit → confirmation dialog appears
- ✅ Confirm → OKR transitions to submitted state
- ✅ Verify in detail page: edit buttons hidden, fields read-only

#### Files to Create/Modify

**Backend**:
- `backend/src/objectives/objectives.controller.ts` (POST /:id/submit)
- `backend/src/objectives/objectives.service.ts` (submitObjective method)

**Frontend**:
- `frontend/src/pages/ObjectiveDetail.tsx` (submit button logic)
- `frontend/src/components/SubmitConfirmationDialog.tsx` (new component)
- `frontend/src/hooks/useObjectives.ts` (add submit mutation)

#### Dependencies

- T-007-KEY-RESULTS-CRUD

#### Definition of Done

- [ ] Endpoint tested (≥4 integration tests)
- [ ] Idempotency verified
- [ ] Visibility change tested (MANAGER query)
- [ ] UI disabled/readonly enforced
- [ ] Confirmation dialog displays
- [ ] Code review pass

---

### T-009: Approval Flow (Manager Approve/Reject with ApprovalLog)

**User Story Link**: US-5 (Scenarios 1-8)  
**Pha**: 4 (Manager Views & Approval)  
**Story Points**: 13  
**Priority**: P2  
**Dependency**: T-008-SUBMIT-OKR-FLOW  

#### Tiêu Chí Chấp Nhận

1. ✅ MANAGER "I manage" tab shows OKR with badge: PENDING, APPROVED, REJECTED
2. ✅ Clicking OKR with PENDING status → detail page với "Approve" + "Reject" buttons
3. ✅ MANAGER clicks "Approve" → approvalStatus=APPROVED, buttons disappear, grade editable
4. ✅ MANAGER clicks "Reject" → form to enter rejection reason
5. ✅ Submit rejection: approvalStatus=REJECTED, isSubmitted=false, ApprovalLog created
6. ✅ After reject, OKR disappears from MANAGER "I manage" until re-submitted
7. ✅ EMPLOYEE calls approve/reject endpoints → 403
8. ✅ EMPLOYEE sees OKR read-only when PENDING; can edit after REJECTED

#### Chi Tiết Thực Hiện

**Backend**:
- POST `/objectives/:id/approve` endpoint
- POST `/objectives/:id/reject` endpoint (accept reason)
- ApprovalLog model (immutable): id, objectiveId, reviewerId, action (ENUM), comment, timestamp
- On reject: transaction sets approvalStatus=REJECTED, isSubmitted=false, creates ApprovalLog

**Frontend**:
- Approval buttons component in detail page
- Rejection form/modal
- Badge display (PENDING/APPROVED/REJECTED)

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ ApprovalLog immutability check

**Integration Tests**:
- ✅ POST /objectives/:id/approve (MANAGER auth) → approvalStatus=APPROVED, ApprovalLog created
- ✅ POST /objectives/:id/approve (EMPLOYEE auth) → 403
- ✅ POST /objectives/:id/reject (MANAGER auth, with reason) → approvalStatus=REJECTED, isSubmitted=false, ApprovalLog with comment
- ✅ After reject, GET /objectives?type=managed (MANAGER) → OKR NOT visible until re-submitted
- ✅ After reject, GET /objectives (EMPLOYEE as owner) → OKR visible as draft (isSubmitted=false)
- ✅ Approve already approved OKR → 400 (invalid state)

**E2E Tests**:
- ✅ MANAGER sees pending OKR badge
- ✅ MANAGER clicks Approve → badge changes to APPROVED, buttons gone
- ✅ MANAGER clicks Reject → form appears for reason input
- ✅ After reject, EMPLOYEE can edit and re-submit

#### Files to Create/Modify

**Backend**:
- `backend/src/approval/approval.controller.ts` (approve/reject endpoints)
- `backend/src/approval/approval.service.ts` (approval logic)
- `backend/src/approval/dto/reject-objective.dto.ts` (reason/comment)
- `backend/src/app.module.ts` (register ApprovalModule)

**Frontend**:
- `frontend/src/pages/ObjectiveDetail.tsx` (approval buttons)
- `frontend/src/components/ApprovalSection.tsx` (approval UI)
- `frontend/src/components/RejectionForm.tsx` (rejection modal)
- `frontend/src/hooks/useApproval.ts` (approve/reject mutations)

**Database**:
- `backend/prisma/schema.prisma` (add ApprovalLog model)
- `backend/prisma/migrations/004_create_approval_logs.sql`
- `backend/prisma/seed.ts` (add sample ApprovalLog entries)

#### Dependencies

- T-008-SUBMIT-OKR-FLOW

#### Definition of Done

- [ ] Approve/reject endpoints tested (≥6 integration tests)
- [ ] ApprovalLog created correctly
- [ ] State transitions validated
- [ ] Visibility changes tested
- [ ] UI displays badges correctly
- [ ] Rejection form functional
- [ ] Code review pass
- [ ] Seed data updated

---

### T-010: Progress Update (KR Progress Tracking with Permission Gates)

**User Story Link**: US-6 (Scenarios 1-6)  
**Pha**: 5 (Detail & Progress)  
**Story Points**: 8  
**Priority**: P2  
**Dependency**: T-009-APPROVAL-FLOW  

#### Tiêu Chí Chấp Nhận

1. ✅ KR detail page shows current progress value + progress bar
2. ✅ approvalStatus=APPROVED → shows "Update Progress" form với input + "Save" button
3. ✅ approvalStatus=PENDING + requester is EMPLOYEE → hide progress form (read-only)
4. ✅ MANAGER can update progress anytime after isSubmitted=true (any approval status)
5. ✅ Input must be trong [startValue, targetValue]; out-of-range rejected với validation error
6. ✅ PATCH `/api/v1/key-results/:id/progress` persists progress value
7. ✅ Non-owner cannot update → 403
8. ✅ Progress field stores numeric value (not percentage); percentage calculated on display

#### Chi Tiết Thực Hiện

**Backend**:
- PATCH endpoint với permission checks on approval status + role
- Service validates progress range [startValue, targetValue]
- Returns validation error if out of range

**Frontend**:
- Conditional form rendering based on permission
- Progress bar component showing percentage calculation

#### Công Việc Test (TDD)

**Unit Tests**:
- ✅ Progress validation (within range, numeric)
- ✅ Percentage calculation: (progress - startValue) / (targetValue - startValue) * 100

**Integration Tests**:
- ✅ PATCH /key-results/:id/progress with approvalStatus=APPROVED (EMPLOYEE) → succeeds
- ✅ PATCH /key-results/:id/progress with approvalStatus=PENDING (EMPLOYEE) → 403
- ✅ PATCH /key-results/:id/progress (MANAGER, submitted=true) → succeeds (any approval status)
- ✅ PATCH /key-results/:id/progress with value > targetValue → 400
- ✅ PATCH /key-results/:id/progress with value < startValue → 400
- ✅ PATCH /key-results/:id/progress with different owner → 403

**E2E Tests**:
- ✅ EMPLOYEE sees progress form only after approval
- ✅ Update progress → progress bar updates
- ✅ Invalid value → error message
- ✅ Progress calculation: 50/100 targetValue → 50% display

#### Files to Create/Modify

**Backend**:
- `backend/src/key-results/key-results.controller.ts` (PATCH /:id/progress)
- `backend/src/key-results/key-results.service.ts` (updateProgress with permission logic)
- `backend/src/key-results/dto/update-progress.dto.ts`

**Frontend**:
- `frontend/src/components/form/ProgressUpdateForm.tsx`
- `frontend/src/pages/KeyResultDetail.tsx`
- `frontend/src/components/ProgressBar.tsx` (visual progress display)
- `frontend/src/hooks/useKeyResults.ts` (add updateProgress mutation)

#### Dependencies

- T-009-APPROVAL-FLOW

#### Definition of Done

- [ ] Permission checks tested (≥5 integration tests)
- [ ] Progress range validation working
- [ ] Progress bar displays correctly
- [ ] Conditional form rendering functional
- [ ] Code review pass

---

### T-011: Members Page (List Employee Personal OKR)

**User Story Link**: US-7 (Scenarios 1-4)  
**Pha**: 4 (Manager Views & Approval)  
**Story Points**: 5  
**Priority**: P2  
**Dependency**: T-004-DASHBOARD-MANAGER-VIEW  

#### Tiêu Chí Chấp Nhận

1. ✅ GET `/api/v1/members` returns Personal OKR từ EMPLOYEE only (isSubmitted=true)
2. ✅ Filters out MANAGER OKR and Team OKR (type=TEAM)
3. ✅ EMPLOYEE direct request /members → 403 or redirect
4. ✅ MANAGER/ADMIN can filter by quarter on Members page
5. ✅ Members page is separate view under sidebar navigation "Members"
6. ✅ Display user name + OKR title + quarter + approval status

#### Chi Tiết Thực Hiện

**Frontend Only** (backend endpoint already in T-004):
- Members.tsx page component
- API call with role guard

#### Công Việc Test (TDD)

**Integration Tests**:
- ✅ GET /members (EMPLOYEE) → 403
- ✅ GET /members (MANAGER) → returns only Personal submitted EMPLOYEE OKR
- ✅ GET /members?quarter=Q2/2026 (MANAGER) → filtered by quarter
- ✅ GET /members (ADMIN) → returns Personal submitted EMPLOYEE OKR

**E2E Tests**:
- ✅ MANAGER clicks "Members" → page loads with list
- ✅ No MANAGER OKR visible
- ✅ No Team OKR visible
- ✅ EMPLOYEE tries /members URL → redirected or 403 shown
- ✅ Quarter filter works

#### Files to Create/Modify

**Frontend**:
- `frontend/src/pages/Members.tsx` (new page)
- Update routing in `frontend/src/App.tsx`
- Update `frontend/src/hooks/useObjectives.ts` (add getMembers query)

#### Dependencies

- T-004-DASHBOARD-MANAGER-VIEW (endpoint already exists)

#### Definition of Done

- [ ] Members page renders correctly
- [ ] Filtering works
- [ ] Access control verified
- [ ] UI displays required fields
- [ ] Code review pass

---

### T-012: Objective Detail Page (Full OKR Information Display)

**User Story Link**: US-8 (Scenarios 1-5)  
**Pha**: 5 (Detail & Progress)  
**Story Points**: 10  
**Priority**: P3  
**Dependency**: T-007-KEY-RESULTS-CRUD, T-009-APPROVAL-FLOW  

#### Tiêu Chí Chấp Nhận

1. ✅ GET `/api/v1/objectives/:id` returns objective + all KR with current progress
2. ✅ Detail page displays: title, description, owner name, quarter, approval status badge
3. ✅ Progress bar shows avg([KR.progress / KR.targetValue]) across all KR; handle division-by-zero
4. ✅ Tab "General Info" shows OKR overview + KR list with individual progress bars
5. ✅ Tab "Grade & Feedback" (MANAGER edit, EMPLOYEE read-only)
6. ✅ EMPLOYEE accessing other user's OKR → 403
7. ✅ Role-based UI: submitted OKR shows read-only fields; editable hidden if submitted

#### Chi Tiết Thực Hiện

**Backend**:
- GET endpoint với full object graph (objective + KRs + owner)
- Authorization check: owner or manager (for manager can see submitted)

**Frontend**:
- Detail page with tabs (General Info, Grade & Feedback, Conversation)
- Role-based conditional rendering
- Progress calculation component

#### Công Việc Test (TDD)

**Integration Tests**:
- ✅ GET /objectives/:id (own OKR, EMPLOYEE) → returns full detail
- ✅ GET /objectives/:id (other user's OKR, EMPLOYEE) → 403
- ✅ GET /objectives/:id (MANAGER, submitted OKR) → full detail
- ✅ Progress calculation: 2 KR với values 50/100, 30/100 → avg = 40%
- ✅ Progress with KR targetValue=0 → doesn't crash (prevented by DB constraint)
- ✅ GET /objectives/:id (MANAGER, non-submitted EMPLOYEE OKR) → 403

**E2E Tests**:
- ✅ Open objective detail → all sections render
- ✅ If submitted, edit buttons hidden
- ✅ If draft, edit buttons visible
- ✅ Progress bar displays correct percentage

#### Files to Create/Modify

**Backend**:
- `backend/src/objectives/objectives.controller.ts` (GET /:id)
- `backend/src/objectives/objectives.service.ts` (getObjectiveDetail)

**Frontend**:
- `frontend/src/pages/ObjectiveDetail.tsx` (main detail page)
- `frontend/src/components/OKRTabs.tsx` (tab switching)
- `frontend/src/components/GeneralInfoTab.tsx`
- `frontend/src/components/ProgressChart.tsx`
- `frontend/src/hooks/useObjectiveDetail.ts` (custom hook)

#### Dependencies

- T-007-KEY-RESULTS-CRUD
- T-009-APPROVAL-FLOW

#### Definition of Done

- [ ] Detail endpoint tested (≥4 integration tests)
- [ ] Progress calculation verified
- [ ] Authorization checked
- [ ] Tabs functional
- [ ] Progress bars display correctly
- [ ] Code review pass

---

### T-013: Grade & Feedback Tab (Manager End-of-Period Feedback)

**User Story Link**: US-8 (Scenarios 3-4)  
**Pha**: 5 (Detail & Progress)  
**Story Points**: 5  
**Priority**: P3  
**Dependency**: T-012-OBJECTIVE-DETAIL-PAGE  

#### Tiêu Chí Chấp Nhận

1. ✅ Tab "Grade & Feedback" displays chỉ for approved OKR
2. ✅ MANAGER can input text field (Grade) and save
3. ✅ EMPLOYEE sees Grade as read-only text (no edit button)
4. ✅ Grade field can store long text (assume 1000 char max)
5. ✅ PATCH `/api/v1/objectives/:id/grade` (MANAGER only) updates + persists
6. ✅ Grade optional (empty allowed)

#### Chi Tiết Thực Hiện

**Backend**:
- Add `grade` field (String, optional, null default) to Objective model
- PATCH endpoint với MANAGER role guard
- Validation: max 1000 char (optional)

**Frontend**:
- TextArea in Grade tab, editable only for MANAGER
- Display-only for EMPLOYEE
- Character count helper

#### Công Việc Test (TDD)

**Integration Tests**:
- ✅ PATCH /objectives/:id/grade (MANAGER auth) → updates grade field
- ✅ PATCH /objectives/:id/grade (EMPLOYEE auth) → 403
- ✅ GET /objectives/:id → grade field included in response
- ✅ PATCH /objectives/:id/grade with 1000+ chars → 400 (validation)

**E2E Tests**:
- ✅ MANAGER enters grade text → saves → reloads → grade persists
- ✅ EMPLOYEE views grade as read-only

#### Files to Create/Modify

**Backend**:
- `backend/src/objectives/objectives.controller.ts` (PATCH /:id/grade)
- `backend/src/objectives/objectives.service.ts` (updateGrade)
- `backend/src/objectives/dto/update-grade.dto.ts`

**Frontend**:
- `frontend/src/components/GradeAndFeedback.tsx` (new component)

**Database**:
- `backend/prisma/schema.prisma` (add grade field to Objective)
- `backend/prisma/migrations/005_add_grade_column.sql`

#### Dependencies

- T-012-OBJECTIVE-DETAIL-PAGE

#### Definition of Done

- [ ] Grade endpoint tested (≥3 integration tests)
- [ ] Read-only UI for EMPLOYEE
- [ ] Persistence verified
- [ ] Character limit enforced
- [ ] Code review pass
- [ ] Migrations applied

---

## RBAC Matrix - Quyền Truy Cập Chi Tiết

| Module | Feature | EMPLOYEE | MANAGER | ADMIN | Task |
|--------|---------|----------|---------|-------|------|
| MOD-01 | Login | ✓ | ✓ | ✓ | T-001 |
| MOD-01 | Refresh Token | ✓ | ✓ | ✓ | T-002 |
| MOD-01 | Logout | ✓ | ✓ | ✓ | T-001 |
| MOD-02 | View own OKR | ✓ | ✓ | ✓ | T-003 |
| MOD-02 | View team OKR (submitted) | ✗ | ✓ | ✓ | T-003/T-004 |
| MOD-02 | View Members page | ✗ (403) | ✓ | ✓ | T-004/T-011 |
| MOD-02 | Access /members endpoint | ✗ (403) | ✓ | ✓ | T-004 |
| MOD-03 | Create Personal OKR | ✓ | ✓ | ✓ | T-006 |
| MOD-03 | Create Team OKR | ✗ (403) | ✓ | ✓ | T-006 |
| MOD-03 | View own draft OKR | ✓ | ✓ | ✓ | T-003/T-004 |
| MOD-03 | Submit OKR | ✓ | ✓ | ✓ | T-008 |
| MOD-03 | Edit OKR (pre-submit) | ✓ (own) | ✓ (own) | ✓ | T-006 |
| MOD-03 | Edit OKR (post-submit) | ✗ (403) | ✗ (403) | ✗ (403) | T-006/T-007/T-008 |
| MOD-03 | Add/Edit/Delete KR (pre-submit) | ✓ (own) | ✓ (own) | ✓ | T-007 |
| MOD-03 | Add/Edit/Delete KR (post-submit) | ✗ (403) | ✗ (403) | ✗ (403) | T-007/T-008 |
| MOD-03 | Update progress (PENDING, EMPLOYEE) | ✗ (403) | ✓ | ✓ | T-010 |
| MOD-03 | Update progress (APPROVED, EMPLOYEE) | ✓ | ✓ | ✓ | T-010 |
| MOD-04 | Approve OKR | ✗ (403) | ✓ | ✓ | T-009 |
| MOD-04 | Reject OKR | ✗ (403) | ✓ | ✓ | T-009 |
| MOD-04 | Edit Grade | ✗ (403) | ✓ | ✓ | T-013 |
| MOD-04 | View Grade | ✓ (read-only) | ✓ | ✓ | T-013 |

---

## API Endpoints Reference (16 endpoints mapped to tasks)

| Method | Endpoint | Task | Role | Description |
|--------|----------|------|------|-------------|
| POST | `/api/v1/auth/login` | T-001 | ANY | Login với email/password |
| POST | `/api/v1/auth/refresh` | T-002 | ANY | Refresh access token |
| POST | `/api/v1/auth/logout` | T-001 | ANY | Logout, clear cookies |
| GET | `/api/v1/objectives` | T-003/T-004 | AUTH | List OKR (filtered by role) |
| POST | `/api/v1/objectives` | T-006 | AUTH | Create Objective |
| GET | `/api/v1/objectives/:id` | T-012 | AUTH | Get Objective detail |
| PATCH | `/api/v1/objectives/:id` | T-006 | AUTH | Update Objective (pre-submit) |
| POST | `/api/v1/objectives/:id/submit` | T-008 | AUTH | Submit Objective |
| POST | `/api/v1/objectives/:id/approve` | T-009 | MGR | Approve Objective |
| POST | `/api/v1/objectives/:id/reject` | T-009 | MGR | Reject Objective |
| PATCH | `/api/v1/objectives/:id/grade` | T-013 | MGR | Update Grade & Feedback |
| GET | `/api/v1/objectives/:id/key-results` | T-007 | AUTH | List KR for Objective |
| POST | `/api/v1/objectives/:id/key-results` | T-007 | AUTH | Create KR |
| PATCH | `/api/v1/key-results/:id` | T-007 | AUTH | Update KR (pre-submit) |
| DELETE | `/api/v1/key-results/:id` | T-007 | AUTH | Delete KR (pre-submit) |
| PATCH | `/api/v1/key-results/:id/progress` | T-010 | AUTH | Update KR progress |
| GET | `/api/v1/members` | T-004/T-011 | MGR | List Employee Personal OKR |

---

## Data Model Reference (4 entities mapped to tasks)

### User Entity
**Tasks**: T-001 (create + seed)  
**Fields**: id, email (unique), name, password (bcrypt), role (ADMIN|MANAGER|EMPLOYEE), createdAt, updatedAt  
**Indexes**: PRIMARY KEY (id), UNIQUE (email), INDEX (role)

### Objective Entity
**Tasks**: T-006, T-008, T-009, T-013  
**Fields**: id, title, description, type (PERSONAL|TEAM), ownerId (FK), quarter, isSubmitted (bool), approvalStatus (PENDING|APPROVED|REJECTED), grade (nullable), createdAt, updatedAt  
**Constraints**: 
- Type: EMPLOYEE only creates PERSONAL; MANAGER can create PERSONAL or TEAM
- isSubmitted: false on creation, true on submit, false on reject
- approvalStatus: PENDING on creation/submission, changed to APPROVED/REJECTED by manager
- Quarter format: Q[1-4]/YYYY
**Indexes**: PRIMARY KEY (id), FK (ownerId), INDEX (quarter), INDEX (ownerId, isSubmitted)

### KeyResult Entity
**Tasks**: T-007, T-010  
**Fields**: id, objectiveId (FK), title, startValue, targetValue, progress, deadline, createdAt, updatedAt  
**Constraints**:
- Max 3 per Objective (enforce in service)
- targetValue > 0 (prevent division-by-zero)
- progress in [startValue, targetValue]
- Post-submit: only progress field updatable
**Indexes**: PRIMARY KEY (id), FK (objectiveId)

### ApprovalLog Entity
**Tasks**: T-009  
**Fields**: id, objectiveId (FK), reviewerId (FK), action (APPROVED|REJECTED), comment (nullable), timestamp  
**Constraints**: Immutable (no update/delete), append-only  
**Indexes**: PRIMARY KEY (id), FK (objectiveId), FK (reviewerId), INDEX (timestamp)

---

## Testing Checklist

### Unit Test Requirements by Module

#### Auth Module (T-001, T-002)
- [ ] bcrypt password hashing/comparison
- [ ] JWT token generation (correct payload, TTL)
- [ ] JWT token validation
- [ ] Rate limiter counter logic
- [ ] Error message consistency (no email enumeration)

#### Dashboard Module (T-003, T-004)
- [ ] OKR filtering by ownerId
- [ ] OKR filtering by isSubmitted status
- [ ] OKR filtering by quarter
- [ ] Role-based query logic
- [ ] Sidebar nav item visibility by role

#### Objective Module (T-006, T-008)
- [ ] CreateObjectiveDto validation (class-validator)
- [ ] Type enum enforcement (EMPLOYEE can't create TEAM)
- [ ] Quarter format regex validation
- [ ] Submit state validation (≥1 KR)
- [ ] Post-submit immutability

#### KeyResult Module (T-007, T-010)
- [ ] KR validation (title, startValue, targetValue)
- [ ] Max 3 KR per Objective check
- [ ] Progress range validation [startValue, targetValue]
- [ ] Post-submit lock enforcement
- [ ] Progress calculation percentage

#### Approval Module (T-009)
- [ ] ApprovalLog creation
- [ ] Reject state transition (isSubmitted reset to false)
- [ ] Approval status enum

### Integration Test Coverage Targets

**Critical Flows (100% coverage)**:
- ✅ Auth login → JWT creation → protected route access
- ✅ Create OKR → submit → manager "I manage" visibility
- ✅ Approve → EMPLOYEE progress update enabled
- ✅ Reject → EMPLOYEE can re-edit
- ✅ Progress update with permission checks

**Services (≥70% coverage)**:
- [ ] ObjectivesService: ≥70% coverage
- [ ] KeyResultsService: ≥70% coverage
- [ ] AuthService: 100% coverage
- [ ] ApprovalService: 100% coverage

**Database Interactions**:
- ✅ Create/read/update operations with Prisma
- ✅ FK constraints validation
- ✅ Unique constraint enforcement (email)
- ✅ Transaction rollback on errors

### E2E Test Scenarios

**Happy Path Flows**:
- [ ] Login → Dashboard → Create OKR → Add KR → Submit → Manager approve → Employee update progress
- [ ] Manager view members list → filter by quarter
- [ ] Manager reject OKR → employee re-edit and re-submit
- [ ] View OKR detail → check progress calculation → check grade display

**Edge Cases**:
- [ ] Create OKR with 0 KR → submit fails
- [ ] Create OKR with 3 KR → add 4th fails
- [ ] Update progress out of range → validation error
- [ ] Concurrent submit same OKR → idempotent
- [ ] Token refresh during request → transparent retry
- [ ] Access token expiry → auto-refresh → no interruption

**Access Control**:
- [ ] EMPLOYEE tries POST /approve → 403
- [ ] EMPLOYEE tries type=TEAM → 403
- [ ] EMPLOYEE tries /members → 403
- [ ] EMPLOYEE tries edit post-submit → 403
- [ ] EMPLOYEE accesses other user OKR → 403

---

## Definition of Done - Tiêu Chí Chung Cho Tất Cả Tasks

Mỗi công việc PHẢI memenuhi tiêu chí sau trước khi merge:

### Code Quality
- [ ] **TDD Discipline**: Test written trước implementation, test fails trước khi code fix
- [ ] **Test Coverage**: Unit tests ≥70%, integration tests cho critical flows ≥100%
- [ ] **TypeScript**: No `any` types, all imports properly typed, `npx tsc --noEmit` passes
- [ ] **Code Review**: ≥1 code review pass (approved), no unresolved comments
- [ ] **Linting**: ESLint + Prettier pass, no warnings

### Functional Requirements
- [ ] Tất cả acceptance criteria (✅) được verify
- [ ] Edge cases từ spec được handle
- [ ] Error messages match spec (Vietnamese, user-friendly)
- [ ] HTTP status codes correct (400 validation, 403 permission, 404 not found, 500 server error)

### Database & Data
- [ ] Prisma schema updated (nếu cần model/field mới)
- [ ] Migrations generated + applied (`npx prisma migrate dev`)
- [ ] Seed data updated với sample records
- [ ] Seed idempotent (running twice no duplicates)

### Documentation
- [ ] Endpoint documentation (Swagger/inline comments)
- [ ] Complex logic có code comments
- [ ] TypeScript interfaces documented (JSDoc comments)

### Testing Verification
- [ ] `npm run test:unit` pass (backend)
- [ ] `npm run test:integration` pass (backend)
- [ ] `npm run test:frontend` pass (if applicable)
- [ ] Manual E2E test completed (Postman/Playwright)
- [ ] No regressions (run full test suite)

### Security & Performance
- [ ] Passwords hashed (bcrypt, cost 12)
- [ ] SQL injection prevented (Prisma parameterized queries)
- [ ] JWT secrets não hardcoded in code (via docker-compose.yml)
- [ ] Sensitive data não logged (@Exclude on password fields)
- [ ] Rate limiting applied (auth endpoints)
- [ ] CORS configured correctly

### Deployment Readiness
- [ ] Docker images build successfully
- [ ] Environment variables não hardcoded (docker-compose.yml)
- [ ] No console.log() (use logger)
- [ ] Error handling: no raw stack traces in API response
- [ ] Graceful shutdown (cleanup resources)

---

## Phân Tích Phụ Thuộc & Đường Dẫn Quan Trọng

### Task Dependency Tree

```
T-001-AUTH-LOGIN (13 pts)
├─→ T-002-AUTH-REFRESH (8 pts)
├─→ T-003-DASHBOARD-EMPLOYEE (8 pts)
│   ├─→ T-005-CREATE-OBJ-FORM (5 pts)
│   │   └─→ T-006-CREATE-OBJ-BACKEND (8 pts)
│   │       ├─→ T-007-KR-CRUD (10 pts)
│   │       │   ├─→ T-008-SUBMIT-FLOW (8 pts)
│   │       │   │   ├─→ T-009-APPROVAL (13 pts)
│   │       │   │   │   └─→ T-010-PROGRESS (8 pts)
│   │       │   │   │       └─→ T-012-DETAIL (10 pts)
│   │       │   │   │           └─→ T-013-GRADE (5 pts)
│   │       │   │   └─→ T-012-DETAIL (10 pts)
│   │       │   │       └─→ T-013-GRADE (5 pts)
├─→ T-004-DASHBOARD-MANAGER (8 pts)
│   ├─→ T-009-APPROVAL (13 pts) [also depends on T-008]
│   └─→ T-011-MEMBERS (5 pts)
└─→ Total: 106 story points
```

### Critical Path (Minimum to deliver value)

**Essential sequence** (79 pts):
```
T-001 (13) → T-003 (8) → T-005 (5) → T-006 (8) → T-007 (10) → 
T-008 (8) → T-009 (13) → T-010 (8) → T-012 (10) → T-013 (5)
```

**Extended path** (all 13 tasks):
- Add T-002 (8 pts): Auto-refresh (important for production-like behavior)
- Add T-004 (8 pts): Manager view of own OKR
- Add T-011 (5 pts): Members page (complete manager workflow)

---

## Timeline & Resource Estimate

### Recommended Phasing (3-4 weeks, 2-3 developers)

| Pha | Tasks | Effort | Timeline | Developers | Dependencies |
|-----|-------|--------|----------|-----------|--------------|
| 1 | T-001, T-002 | 21 pts | Week 1 | 1-2 | None |
| 2 | T-003, T-005, T-006 | 21 pts | Week 1-2 | 1-2 | Phase 1 |
| 3 | T-007, T-008 | 18 pts | Week 2 | 1-2 | Phase 2 |
| 4 | T-004, T-009, T-011 | 26 pts | Week 2-3 | 2 | Phases 1-3 |
| 5 | T-010, T-012, T-013 | 23 pts | Week 3-4 | 1-2 | Phase 4 |

### Risk Areas & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| JWT refresh complexity | High | Early integration testing, interceptor unit tests |
| Permission gates scattered | Medium | Centralized RolesGuard, decorator-based approach |
| Progress calculation (division-by-zero) | Low | DB constraint targetValue > 0, app validation |
| Concurrent submit idempotency | Medium | Database unique constraint + app-level check |
| Type enforcement (EMPLOYEE + TEAM) | Medium | Test EMPLOYEE trying to bypass in E2E |

---

## Next Steps

1. **Prepare Test Environment**: Docker-compose up, seed data, Postman collection
2. **Phase 1 Kickoff**: Assign T-001 + T-002 to lead developer
3. **Code Review Process**: Establish PR review checklist
4. **Testing**: Run integration + E2E tests after each task
5. **Documentation**: Keep CLAUDE.md updated with architecture decisions

---

## Glossary (Vietnamese/English)

| Viết tắt | Tiếng Việt | Tiếng Anh | Giải Thích |
|----------|-----------|----------|-----------|
| OKR | Objectives & Key Results | OKR | Mục tiêu chiến lược + đo lường kết quả |
| KR | Key Result | KR | Kết quả chính (đo lường) |
| RBAC | Kiểm soát truy cập dựa trên vai trò | Role-Based Access Control | Quyền hạn dựa trên vai trò user |
| JWT | Token Web JSON | JSON Web Token | Xác thực stateless với token |
| TTL | Thời gian tồn tại | Time To Live | Thời gian hết hạn token |
| TDD | Phát triển dựa vào test | Test-Driven Development | Viết test trước, code sau |
| DTO | Đối tượng truyền dữ liệu | Data Transfer Object | Schema validate input/output |
| CRUD | Tạo, Đọc, Cập nhật, Xóa | Create, Read, Update, Delete | 4 thao tác cơ bản |
| E2E | Đầu-cuối | End-to-End | Test toàn flow người dùng |

---

## Document Metadata

- **Created**: 2026-07-02
- **Last Updated**: 2026-07-02
- **Version**: 1.0.0
- **Owner**: Product Team
- **Status**: Ready for Implementation
- **Next Review**: After Phase 1 Completion
