# Feature Specification: OKR Web Application

**Feature Branch**: `001-okr-webapp`  
**Created**: 2026-07-01  
**Status**: Draft  
**Language**: Vietnamese  
**Nguồn SRS**: `docs/output/ipa-docs/srs/srs-mod00-okr-webapp.md`  
**Nguồn BD**: `docs/output/ipa-docs/bd/bd-mod00-okr-webapp.md`  
**Run ID**: ui-e14d6a8472

> Tài liệu này mô tả **những gì hệ thống phải làm và tại sao hành vi đó quan trọng**. Không đề cập chi tiết triển khai ngoại trừ các ràng buộc được nêu rõ trong yêu cầu kỹ thuật.

---

## User Scenarios & Testing *(mandatory)*

### Test-First Delivery Rules (Bắt buộc — TDD Strict)

- **Quy tắc bất di bất dịch:** Mọi hành vi được triển khai PHẢI có test được viết TRƯỚC và được quan sát THẤT BẠI vì đúng lý do trước khi viết code thực
- Tests PHẢI bao phủ: HTTP status code, hình dạng response, thay đổi trạng thái DB thực (đọc lại sau khi ghi)
- Tests xác thực PHẢI kiểm tra: chưa xác thực → 401, sai role → 403, vi phạm quyền sở hữu → 403
- Pseudo-tests (luôn pass, mock tất cả, không có assertion) là lỗi review CRITICAL
- Integration tests PHẢI dùng database thực — mock in-memory bị CẤM
- Red-green-refactor là chu kỳ bắt buộc: test thất bại → code tối thiểu để pass → refactor

---

### User Story 1 — Đăng nhập và bảo vệ phiên làm việc (Priority: P1)

Một người dùng muốn đăng nhập bằng email và mật khẩu để truy cập hệ thống OKR. Khi phiên hết hạn, hệ thống tự động làm mới token mà không yêu cầu người dùng đăng nhập lại. Khi người dùng đăng xuất, phiên bị xóa hoàn toàn.

**Why this priority**: Đây là cổng vào của toàn bộ hệ thống. Mọi chức năng khác đều phụ thuộc vào xác thực thành công. Không có đăng nhập thì không có OKR.

**Independent Test**: Có thể test hoàn toàn bằng cách gửi `POST /api/v1/auth/login` với thông tin hợp lệ/không hợp lệ và xác minh phản hồi.

**Acceptance Scenarios**:

1. **Given** người dùng chưa đăng nhập, **When** truy cập bất kỳ route nào ngoại trừ `/login`, **Then** hệ thống chuyển hướng về `/login`
2. **Given** người dùng nhập email và mật khẩu hợp lệ, **When** nhấn "Sign in", **Then** hệ thống đặt Access Token (TTL 1h) và Refresh Token (TTL 7d) vào HttpOnly cookie, redirect về Dashboard
3. **Given** người dùng nhập email không tồn tại hoặc mật khẩu sai, **When** nhấn "Sign in", **Then** hệ thống hiển thị thông báo lỗi chung "Email hoặc mật khẩu không đúng" (không phân biệt loại lỗi)
4. **Given** Access Token hết hạn trong khi người dùng đang thao tác, **When** frontend nhận 401, **Then** hệ thống tự động gọi `/auth/refresh`, thử lại request ban đầu, người dùng không thấy gián đoạn
5. **Given** cả Access Token và Refresh Token đều hết hạn, **When** hệ thống thử refresh, **Then** xóa cookies và redirect về `/login` với thông báo "Phiên làm việc đã hết hạn"
6. **Given** người dùng đã đăng nhập, **When** nhấn "Logout", **Then** cookies bị xóa và redirect về `/login`; nhấn Back trình duyệt phải về `/login`
7. **Given** cùng IP gửi quá 60 request/phút đến `/auth/login`, **When** vượt ngưỡng, **Then** hệ thống trả về HTTP 429 "Thử lại sau ít phút"

---

### User Story 2 — Dashboard OKR với kiểm soát theo role (Priority: P1)

Một EMPLOYEE muốn thấy OKR của mình (bao gồm cả bản nháp chưa submit). Một MANAGER muốn thấy tất cả OKR đã submit của team. Sidebar điều hướng phải hiển thị đúng theo role — EMPLOYEE không được thấy link "Members" và "OKR-all".

**Why this priority**: Dashboard là màn hình chính người dùng tương tác hàng ngày. Kiểm soát hiển thị theo role (CR-0404) là yêu cầu bắt buộc từ nghiệp vụ.

**Independent Test**: Có thể test bằng cách đăng nhập với EMPLOYEE và MANAGER, kiểm tra danh sách OKR hiển thị và cấu trúc sidebar.

**Acceptance Scenarios**:

1. **Given** EMPLOYEE đăng nhập, **When** vào Dashboard, **Then** chỉ thấy OKR của mình (bao gồm bản nháp) — không thấy OKR của người khác
2. **Given** EMPLOYEE đăng nhập, **When** xem sidebar, **Then** link "Members" và "OKR-all" KHÔNG hiển thị (không render DOM, không chỉ ẩn bằng opacity)
3. **Given** MANAGER đăng nhập, **When** vào Dashboard, **Then** thấy tất cả OKR đã submit (`isSubmitted=true`) trong "I manage"
4. **Given** MANAGER đăng nhập, **When** xem sidebar, **Then** thấy cả "I created", "I manage", "Members", và "OKR-all"
5. **Given** EMPLOYEE cố truy cập URL `/members` trực tiếp, **When** request đến server, **Then** hệ thống trả về 403 hoặc redirect về Dashboard
6. **Given** không có OKR nào, **When** vào Dashboard, **Then** hiển thị trạng thái rỗng: "Chưa có OKR nào. Nhấn NEW OKR để tạo mới."
7. **Given** người dùng chọn filter Quarter, **When** chọn kỳ quý khác, **Then** danh sách OKR cập nhật theo kỳ đã chọn

---

### User Story 3 — Tạo Objective với Type Personal/Team (Priority: P1)

Một người dùng muốn tạo Objective mới. EMPLOYEE chỉ được tạo Personal OKR. MANAGER có thể chọn Personal (cho bản thân) hoặc Team (cho cả nhóm). Trường Owner không còn hiển thị — hệ thống tự động gán từ JWT.

**Why this priority**: Tạo Objective là điểm khởi đầu của mọi OKR workflow. CR-0406 thay đổi trực tiếp form này.

**Independent Test**: Có thể test bằng cách gửi `POST /api/v1/objectives` với các role khác nhau và kiểm tra response.

**Acceptance Scenarios**:

1. **Given** EMPLOYEE ở form tạo Objective, **When** xem dropdown Type, **Then** chỉ thấy "Personal" và không thể thay đổi
2. **Given** MANAGER ở form tạo Objective, **When** xem dropdown Type, **Then** thấy cả "Personal" và "Team"
3. **Given** EMPLOYEE nhập title, chọn Type=Personal, chọn Quarter, **When** nhấn "Save", **Then** Objective được tạo với `isSubmitted=false`, `ownerId` tự động từ JWT, redirect đến trang chi tiết
4. **Given** EMPLOYEE cố gửi request tạo Objective với `type=TEAM` (bypass frontend), **When** backend nhận request, **Then** trả về HTTP 403
5. **Given** người dùng nhập Quarter sai format (ví dụ "Q2-2026"), **When** submit form, **Then** hiển thị lỗi "Format phải là Q2/2026"
6. **Given** người dùng không nhập Title, **When** submit form, **Then** hiển thị lỗi "Tiêu đề không được trống"
7. **Given** Objective được tạo thành công, **When** MANAGER xem danh sách, **Then** KHÔNG thấy Objective này (vì `isSubmitted=false`)

---

### User Story 4 — Thêm Key Result và Submit OKR (Priority: P1)

Một người dùng muốn thêm Key Results vào Objective (tối đa 3 KR), sau đó Submit OKR cho Manager xem xét. Sau khi Submit, toàn bộ cấu trúc OKR bị khóa — không thể sửa.

**Why this priority**: Submit flow là trung tâm của workflow phê duyệt. CR-0405 định nghĩa toàn bộ quy tắc này.

**Independent Test**: Có thể test bằng cách tạo Objective, thêm KR, submit và kiểm tra trạng thái.

**Acceptance Scenarios**:

1. **Given** Objective có 0-2 KR, **When** nhấn "Add Key Result", **Then** form thêm KR hiển thị
2. **Given** Objective đã có 3 KR, **When** xem trang chi tiết, **Then** nút "Add Key Result" bị ẩn hoặc disabled với thông báo "Đã đạt giới hạn 3 Key Results"
3. **Given** Objective có ít nhất 1 KR, **When** nhấn "Submit OKR", **Then** hộp thoại xác nhận: "Sau khi submit, bạn không thể chỉnh sửa KR. Tiếp tục?"
4. **Given** người dùng xác nhận Submit, **When** `POST /api/v1/objectives/:id/submit`, **Then** `isSubmitted=true`, `approvalStatus=PENDING`, OKR xuất hiện trong danh sách Manager
5. **Given** Objective có 0 KR, **When** xem trang chi tiết, **Then** nút "Submit OKR" bị disabled với thông báo "Cần ít nhất 1 KR để submit"
6. **Given** Objective đã submit (`isSubmitted=true`), **When** owner xem chi tiết, **Then** nút Add KR, Edit KR, Delete KR đều bị ẩn; fields Title/Description là read-only
7. **Given** Objective đã submit, **When** request backend thử sửa Title/Description, **Then** backend trả về HTTP 403
8. **Given** Objective đã submit, **When** OKR chưa submit của người khác, **Then** MANAGER không thấy OKR đó trong bất kỳ query nào

---

### User Story 5 — Phê duyệt OKR (Manager Approve/Reject) (Priority: P2)

Một MANAGER muốn xem danh sách OKR đã được submit bởi nhân viên, phê duyệt hoặc từ chối chúng. Khi Approve, nhân viên chỉ được cập nhật tiến độ. Khi Reject, nhân viên có thể chỉnh sửa và submit lại.

**Why this priority**: Phê duyệt là bước quan trọng nhưng phụ thuộc vào Submit (P1). Không có Submit thì không có Approve.

**Independent Test**: Test bằng cách submit OKR với EMPLOYEE, đăng nhập MANAGER, thực hiện approve/reject.

**Acceptance Scenarios**:

1. **Given** MANAGER đăng nhập, **When** vào "My OKRs > I manage", **Then** thấy danh sách OKR với `isSubmitted=true` và badge PENDING/APPROVED/REJECTED
2. **Given** OKR có `approvalStatus=PENDING`, **When** MANAGER xem chi tiết, **Then** thấy nút "Approve" và "Reject"
3. **Given** MANAGER nhấn "Approve", **When** xác nhận, **Then** `approvalStatus=APPROVED`, badge cập nhật, nút Approve/Reject biến mất; EMPLOYEE chỉ được cập nhật progress
4. **Given** MANAGER nhấn "Reject", **When** nhập lý do và xác nhận, **Then** `approvalStatus=REJECTED`, lý do được ghi vào ApprovalLog
5. **Given** OKR bị Reject (TBC-08 resolved: isSubmitted reset về false), **When** EMPLOYEE xem OKR, **Then** có thể chỉnh sửa và submit lại
6. **Given** EMPLOYEE cố gọi `POST /objectives/:id/approve`, **When** backend xử lý, **Then** trả về HTTP 403
7. **Given** OKR đã `approvalStatus=APPROVED`, **When** xem trang chi tiết, **Then** nút Approve/Reject không hiển thị

---

### User Story 6 — Cập nhật tiến độ Key Result (Priority: P2)

Một người dùng muốn cập nhật tiến độ (progress) của Key Result theo tuần. EMPLOYEE chỉ được cập nhật sau khi OKR được Approve. MANAGER có thể cập nhật ngay khi OKR đã Submit.

**Why this priority**: Theo dõi tiến độ là chức năng định kỳ, phụ thuộc vào Approve flow (P2).

**Independent Test**: Test bằng cách approved một OKR với EMPLOYEE và gọi `PATCH /key-results/:id/progress`.

**Acceptance Scenarios**:

1. **Given** OKR đã `approvalStatus=APPROVED`, **When** EMPLOYEE vào KR Detail, **Then** thấy form cập nhật progress và nút "Save"
2. **Given** EMPLOYEE nhập giá trị progress và comment, **When** nhấn "Save", **Then** `PATCH /api/v1/key-results/:id/progress` cập nhật thành công, progress bar refresh
3. **Given** OKR `approvalStatus=PENDING`, **When** EMPLOYEE xem KR Detail, **Then** nút "Save" bị ẩn (chưa được approve)
4. **Given** MANAGER xem KR Detail, **When** OKR đã `isSubmitted=true`, **Then** có thể cập nhật progress
5. **Given** người dùng nhập progress ngoài range [0, targetValue], **When** submit, **Then** hệ thống từ chối với thông báo lỗi hợp lệ
6. **Given** người khác (không phải owner) cố cập nhật progress, **When** gọi API, **Then** backend trả về HTTP 403

---

### User Story 7 — Trang Members (chỉ Manager/Admin) (Priority: P2)

Một MANAGER muốn xem OKR của các nhân viên (không bao gồm OKR của Manager hoặc Team OKR).

**Why this priority**: Chức năng quản lý team, phụ thuộc vào cơ chế sidebar (P1) nhưng là view riêng biệt.

**Independent Test**: Test bằng cách đăng nhập MANAGER, truy cập `/members`, kiểm tra chỉ thấy EMPLOYEE OKR.

**Acceptance Scenarios**:

1. **Given** MANAGER nhấn link "Members" trong sidebar, **When** `/members` load, **Then** chỉ thấy OKR Personal của EMPLOYEE (`ownerRole=EMPLOYEE`, `isSubmitted=true`)
2. **Given** Members page, **When** MANAGER xem danh sách, **Then** KHÔNG thấy OKR của MANAGER hoặc Team OKR (type=TEAM)
3. **Given** EMPLOYEE cố truy cập `/members` qua URL, **When** request gửi đến backend, **Then** backend trả về 403 hoặc redirect

---

### User Story 8 — Xem chi tiết OKR và Grade & Feedback (Priority: P3)

Người dùng muốn xem chi tiết Objective kèm các KR. MANAGER muốn ghi Grade & Feedback cuối kỳ. EMPLOYEE chỉ xem (read-only) phần Grade.

**Why this priority**: Chức năng quan trọng nhưng phụ thuộc vào toàn bộ approve flow.

**Independent Test**: Test bằng cách xem chi tiết OKR và kiểm tra phần Grade & Feedback.

**Acceptance Scenarios**:

1. **Given** người dùng nhấn OKR card, **When** trang `/objectives/:id` load, **Then** thấy tiêu đề, progress tổng hợp (avg KRs), Owner, Quarter, Status, các tab
2. **Given** Tab "General Info" được chọn, **When** xem, **Then** thấy OKR Overview + danh sách KR với progress bar từng KR
3. **Given** MANAGER xem tab "Grade & Feedback", **When** OKR đã approved, **Then** có thể nhập text grade và lưu
4. **Given** EMPLOYEE xem tab "Grade & Feedback", **When** bất kỳ trạng thái, **Then** read-only (không có form nhập)
5. **Given** EMPLOYEE cố truy cập URL `/objectives/:id` của người khác, **When** backend xử lý, **Then** trả về HTTP 403

---

### Edge Cases

- **Concurrent submit:** Nếu hai session cùng submit một OKR, hệ thống chỉ cho phép submit một lần (idempotent)
- **KR với targetValue=0:** Hệ thống xử lý division-by-zero khi tính progress%
- **Quarter boundary:** User tạo OKR cho kỳ quý trong tương lai — không có ràng buộc về kỳ quý phải là hiện tại
- **Reject → re-submit:** Sau khi bị Reject, `isSubmitted` reset về `false`; MANAGER không thấy OKR trong danh sách nữa cho đến khi submit lại
- **Token expiry trong khi submit:** Nếu Access Token hết hạn ngay khi gửi submit request, interceptor tự refresh trước khi retry
- **Empty description:** Trường description là tùy chọn; nếu rỗng, backend lưu `null` (không lưu empty string)

---

## Requirements *(mandatory)*

### Functional Requirements

#### MOD-01: Access & Authentication

- **FR-001**: Hệ thống PHẢI cho phép đăng nhập bằng email + password; xác minh thông qua bcrypt so sánh hash
- **FR-002**: Hệ thống PHẢI phát hành Access Token (TTL 1h) và Refresh Token (TTL 7d) lưu trong HttpOnly, SameSite=Strict cookie
- **FR-003**: Hệ thống PHẢI tự động làm mới Access Token khi nhận HTTP 401, trong suốt với người dùng
- **FR-004**: Hệ thống PHẢI xóa cookies và chuyển về `/login` khi Refresh Token hết hạn
- **FR-005**: Hệ thống PHẢI áp dụng rate limiting 60 req/phút/IP tại endpoint đăng nhập
- **FR-006**: Hệ thống PHẢI thực thi RBAC: EMPLOYEE chỉ truy cập tài nguyên của mình; MANAGER truy cập tất cả OKR đã submit; ADMIN toàn quyền
- **FR-007**: Hệ thống PHẢI bảo vệ tất cả route ngoại trừ `/login` bằng `ProtectedRoute`; người dùng chưa xác thực phải redirect về `/login`

#### MOD-02: Workspace & Dashboard

- **FR-011**: Hệ thống PHẢI hiển thị dashboard với sidebar, header, danh sách OKR phù hợp role ngay sau đăng nhập
- **FR-012**: Hệ thống PHẢI ẩn hoàn toàn link "Members" và "OKR-all" khỏi sidebar của EMPLOYEE (không render DOM)
- **FR-013**: Hệ thống PHẢI hiển thị "Members" và "OKR-all" trong sidebar của MANAGER/ADMIN
- **FR-014**: Hệ thống PHẢI ngăn EMPLOYEE truy cập `/members` (HTTP 403 từ backend)
- **FR-015**: Hệ thống PHẢI cho phép lọc danh sách OKR theo Quarter (format Q[1-4]/YYYY)
- **FR-016**: Trang Members PHẢI chỉ hiển thị OKR Personal của EMPLOYEE (`isSubmitted=true`), không bao gồm OKR MANAGER hoặc Team OKR

#### MOD-03: Objective & Key Result Management

- **FR-026**: Hệ thống PHẢI cho phép tạo Objective với fields: Title (bắt buộc), Description (tùy chọn), Type (bắt buộc), Quarter (bắt buộc); KHÔNG có trường Owner
- **FR-027**: Hệ thống PHẢI tự động gán `ownerId` từ JWT token khi tạo Objective
- **FR-028**: EMPLOYEE chỉ được tạo Objective với `type=PERSONAL`; backend PHẢI từ chối `type=TEAM` từ EMPLOYEE với HTTP 403
- **FR-029**: MANAGER PHẢI được chọn `type=PERSONAL` hoặc `type=TEAM` khi tạo Objective
- **FR-030**: Objective mới được tạo với `isSubmitted=false`; chỉ người tạo mới thấy
- **FR-031**: Hệ thống PHẢI giới hạn tối đa 3 Key Results cho mỗi Objective; backend enforce với HTTP 400 khi vượt quá
- **FR-032**: Hệ thống PHẢI cho phép Submit OKR khi Objective có ≥ 1 KR; nút Submit disabled khi không có KR
- **FR-033**: Submit là hành động một chiều: sau submit (`isSubmitted=true`), KHÔNG thể sửa Title, Description, thêm/sửa/xóa KR; backend enforce HTTP 403
- **FR-034**: Hệ thống PHẢI hiển thị hộp thoại xác nhận trước khi Submit, thông báo hậu quả của hành động
- **FR-035**: Hệ thống PHẢI chỉ cho phép cập nhật `progress` của KR sau khi submit; EMPLOYEE chỉ được cập nhật sau khi OKR được APPROVED
- **FR-036**: Hệ thống PHẢI ngăn mọi thao tác cấu trúc KR sau khi `approvalStatus=APPROVED` (trừ cập nhật progress)

#### MOD-04: Review & Collaboration

- **FR-046**: Hệ thống PHẢI cho phép MANAGER xem tất cả OKR có `isSubmitted=true`; OKR `isSubmitted=false` không xuất hiện trong bất kỳ query MANAGER nào
- **FR-047**: Hệ thống PHẢI cho phép MANAGER Approve OKR với `approvalStatus=PENDING`; sau approve: `approvalStatus=APPROVED`, ghi ApprovalLog
- **FR-048**: Hệ thống PHẢI cho phép MANAGER Reject OKR, nhập lý do từ chối; sau reject: `approvalStatus=REJECTED`, `isSubmitted` reset về `false`, ghi ApprovalLog
- **FR-049**: Hệ thống PHẢI hiển thị tab "Grade & Feedback" trong OKR Detail; MANAGER nhập được, EMPLOYEE chỉ đọc
- **FR-050**: Hệ thống PHẢI ghi ApprovalLog mỗi khi có hành động Approve hoặc Reject, lưu: reviewerId, action, comment, timestamp

### Clarifications Needed

Các điều khoản sau đã được AUTO-RESOLVED (xem `docs/output/ipa-docs/srs/srs-mod00-okr-webapp.md §13`):

- **TBC-03 [AUTO-RESOLVED: High]**: Công thức tính progress Objective = `avg(KR.progress / KR.targetValue * 100)` của tất cả KR
- **TBC-07 [AUTO-RESOLVED: Med]**: Grade là text field tự do để Manager nhập đánh giá
- **TBC-08 [AUTO-RESOLVED: High]**: Sau khi Reject, EMPLOYEE CÓ THỂ sửa và submit lại; `isSubmitted` reset về `false`

Các điều khoản còn placeholder:
- **TBC-01**: "Forgot Password" — placeholder UI, không triển khai logic thực
- **TBC-02**: Tab "Conversation" — render tab nhưng nội dung rỗng
- **TBC-04**: Icon chuông thông báo — render icon tĩnh, không có functionality

### Key Entities

- **User**: Tài khoản người dùng với role (ADMIN/MANAGER/EMPLOYEE), email, password (bcrypt hashed)
- **Objective**: Mục tiêu OKR với vòng đời rõ ràng: draft → submitted → approved/rejected; thuộc sở hữu một User; có Type (PERSONAL/TEAM)
- **KeyResult**: Kết quả đo lường liên kết với Objective; có tiến độ (progress trong range [startValue, targetValue]); mỗi Objective tối đa 3 KR
- **ApprovalLog**: Lịch sử các hành động Approve/Reject do Manager thực hiện; không thể sửa/xóa
- **Quarter**: Kỳ OKR theo format `Q[1-4]/YYYY` (ví dụ: `Q2/2026`)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Người dùng hoàn thành đăng nhập và xem Dashboard trong dưới 3 bước; API response < 2 giây
- **SC-002**: EMPLOYEE tạo Objective, thêm 1-3 KR, và Submit trong dưới 5 phút kể từ đăng nhập
- **SC-003**: MANAGER phê duyệt 1 OKR (Approve hoặc Reject với lý do) trong dưới 2 phút kể từ khi xem
- **SC-004**: Mọi vi phạm RBAC (EMPLOYEE truy cập `/members`, tạo Team OKR, approve) đều bị từ chối với HTTP 403 — 100% không có bypass
- **SC-005**: Sau Submit, tất cả thao tác sửa cấu trúc OKR đều bị khóa — 100% enforce ở cả frontend (ẩn UI) và backend (HTTP 403)
- **SC-006**: Dashboard load trong < 2 giây với 50 OKR items
- **SC-007**: Unit test coverage cho backend services ≥ 70%; critical flows (auth, submit, approve) đạt 100% integration coverage
- **SC-008**: Tất cả 5 màn hình (S-01 đến S-05) có thể truy cập và hiển thị dữ liệu từ database (không có mock data)

---

## Traceability Matrix

| User Story | FEA IDs | Screen | Module |
|------------|---------|--------|--------|
| US-1 (Đăng nhập) | FEA-001, FEA-002, FEA-003, FEA-004, FEA-005, FEA-006, FEA-007, FEA-008 | S-01 | MOD-01 |
| US-2 (Dashboard/Role) | FEA-011, FEA-012, FEA-013, FEA-014, FEA-015, FEA-016, FEA-017, FEA-018, FEA-019, FEA-020 | S-02, S-06 | MOD-02 |
| US-3 (Tạo Objective) | FEA-026, FEA-036, FEA-037 | S-04 | MOD-03 |
| US-4 (KR + Submit) | FEA-027, FEA-028, FEA-029, FEA-030, FEA-033, FEA-034, FEA-035, FEA-039 | S-03 | MOD-03 |
| US-5 (Approve/Reject) | FEA-046, FEA-047, FEA-048 | S-03 | MOD-04 |
| US-6 (Cập nhật progress) | FEA-031, FEA-038 | S-03, S-05 | MOD-03 |
| US-7 (Members page) | FEA-015, FEA-014 | S-06 | MOD-02 |
| US-8 (Chi tiết + Grade) | FEA-032, FEA-049, FEA-050, FEA-051, FEA-052 | S-03 | MOD-04 |

---

## [AUTO-RESOLVED] Assumptions

| # | TBC ID | Câu hỏi | Câu trả lời | Lý do | Độ tin cậy |
|---|--------|---------|-------------|-------|------------|
| 1 | TBC-03 | Công thức tính progress Objective? | `avg(KR.progress / KR.targetValue * 100)` | Phổ biến trong OKR tools, đơn giản rõ ràng | High |
| 2 | TBC-05 | Tự động chuyển status OKR? | Không tự động — manual | Tránh business logic phức tạp, progress và status tách biệt | High |
| 3 | TBC-06 | Team OKR chọn thành viên cụ thể? | Toàn bộ team, không chọn cụ thể | CR-0406 không đề cập chọn thành viên | Med |
| 4 | TBC-07 | Thang điểm Grade? | Text field tự do | Đơn giản, linh hoạt nhất cho workshop | Med |
| 5 | TBC-08 | Sau reject, Employee sửa được? | Có — reset `isSubmitted=false` | Luồng phê duyệt thông thường cho phép chỉnh sửa sau từ chối | High |

---

<!-- STEP-RESULT
step: 3
agent: speckit.specify
status: SUCCESS
feature-id: 001-okr-webapp
module-id: mod00
artifacts:
  spec: specs/001-okr-webapp/spec.md
  report: docs/output/output_logs/001-okr-webapp/reports/03-specify-report.md
metrics:
  user-story-count: 8
  fr-count: 30
  sc-count: 8
  tbc-resolved: 5
  tbc-remaining: 3
verdict: N/A
critical-issues: []
next-inputs:
  spec-path: specs/001-okr-webapp/spec.md
/STEP-RESULT -->
