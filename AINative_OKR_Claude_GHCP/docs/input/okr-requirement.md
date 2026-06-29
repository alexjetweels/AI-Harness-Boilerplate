# REQUIREMENT DEFINITION DOCUMENT

## Hệ thống quản lý OKR (Objectives and Key Results)

---

## 1. Tổng quan hệ thống (System Overview)

### 1.1 Mục đích

Tài liệu này được sử dụng cho workshop nhằm minh họa cách dùng AI Native để làm một hệ thống web OKR.

### 1.2 Phạm vi hệ thống

Hệ thống hỗ trợ:

* Thiết lập OKR theo cấp (Company / Department / Individual)
* Theo dõi tiến độ
* Đánh giá kết quả
* Hiển thị dashboard

### 1.3 Định nghĩa thuật ngữ

| Thuật ngữ  | Mô tả                      |
| ---------- | -------------------------- |
| OKR        | Objectives and Key Results |
| Objective  | Mục tiêu định tính         |
| Key Result | Kết quả định lượng         |
| Progress   | Tiến độ (%)                |

---

## 2. Stakeholders

| Vai trò  | Mô tả                       |
| -------- | --------------------------- |
| Admin    | Quản trị hệ thống           |
| Manager  | Quản lý, phê duyệt OKR      |
| Employee | Tạo và cập nhật OKR cá nhân |

---

## 3. Tổng quan nghiệp vụ (Business Overview)

### 3.1 Business Flow

1. User đăng nhập
2. Tạo Objective
3. Tạo Key Results
4. Manager phê duyệt
5. User cập nhật tiến độ hàng tuần
6. Đánh giá cuối kỳ

---

## 4. Use Case Definition (IPA style)

### UC-01: Tạo Objective

| Item           | Nội dung                        |
| -------------- | ------------------------------- |
| Actor          | Employee                        |
| Description    | Tạo Objective mới               |
| Pre-condition  | User đã đăng nhập               |
| Post-condition | Objective được lưu vào hệ thống |

**Main Flow:**

1. User chọn "Create Objective"
2. Nhập tiêu đề và mô tả
3. Nhấn Save

**Exception Flow:**

* Nếu thiếu thông tin → hiển thị lỗi

---

### UC-02: Cập nhật tiến độ Key Result

| Item        | Nội dung            |
| ----------- | ------------------- |
| Actor       | Employee            |
| Description | Cập nhật tiến độ KR |

**Main Flow:**

1. Chọn Key Result
2. Nhập % tiến độ
3. Lưu

---

## 5. Functional Requirements

| ID    | Tên               | Mô tả                |
| ----- | ----------------- | -------------------- |
| FR-01 | Login             | Người dùng đăng nhập |
| FR-02 | Create Objective  | Tạo Objective        |
| FR-03 | Create Key Result | Tạo KR               |
| FR-04 | Update Progress   | Cập nhật tiến độ     |
| FR-05 | Dashboard         | Hiển thị OKR         |

---

## 6. Screen Definition (画面定義)

### SCR-00: Login Screen

| Item   | Nội dung                    |
| ------ | --------------------------- |
| Mô tả  | Màn hình đăng nhập hệ thống |
| Input  | Username/Email, Password    |
| Action | Sign in, Forgot password    |

### UI Mockup (Login - popup/standalone, không có sidebar)

```
+------------------------------------------------------+
|                     [ Logo ]                         |
|                 Sign in to OKR                       |
|------------------------------------------------------|
| Username or email address                            |
| [______________________________________________]     |
|                                                      |
| Password                              Forgot password?|
| [______________________________________________]     |
|                                                      |
|             [       Sign in        ]                 |
+------------------------------------------------------+
```

---

### SCR-01: Dashboard / OKR List (Left Navigation + List)

| Item       | Nội dung                                                       |
| ---------- | -------------------------------------------------------------- |
| Mô tả      | Hiển thị danh sách OKR theo kỳ (Quarter), bộ lọc và navigation |
| Thành phần | Sidebar, Filter bar, OKR list                                  |

### UI Mockup (Dashboard)

```
+----------------------------------------------------------------------------------+
| FOKR | [All FPT v]   [Search.....................]        [NEW OKR] [ENG v] [🔔] |
+----------------------------------------------------------------------------------+
| Sidebar            | Filter Bar                                           |
|--------------------|------------------------------------------------------|
| 2026               | [Q2/2026 v] [Filters] [⚙]                            |
| My OKRs            |------------------------------------------------------|
| - I created        | OKR LIST                                             |
| - I manage         |------------------------------------------------------|
| Members            | Q2.1: AI for All...   [Not graded]                  |
| OKR - all          | Q1.1: XYZ project...           [Success 100%]       |
|--------------------|------------------------------------------------------|
```

---

### SCR-02: OKR Detail Screen

| Item       | Nội dung                                     |
| ---------- | -------------------------------------------- |
| Mô tả      | Hiển thị chi tiết Objective + Key Results    |
| Thành phần | Objective title, tabs, OKR overview, KR list |

### UI Mockup (OKR Detail)

```
+----------------------------------------------------------------------------------+
| FOKR | [All FPT v]   [Search.....................]        [NEW OKR] [ENG v] [🔔] |
+----------------------------------------------------------------------------------+
| Sidebar            | OKR Detail                                                 |
|--------------------|------------------------------------------------------------|
| 2026               | Objective Title:                                           |
| My OKRs            | 1. POC AI for SQL Injection ...                            |
| - I created        | [REPORT] [OPTIONS]                                         |
| - I manage         |------------------------------------------------------------|
| Members            | Tabs: [General Info] [Conversation] [Grade & Feedback]     |
| OKR - all          |------------------------------------------------------------|
|--------------------| OKR Overview                                               |
|                    | Progress: Not reported yet                                |
|                    | Owner: Nguyen Van A                                   |
|                    | Update due: 30-Jun-2026                                   |
|                    |------------------------------------------------------------|
|                    | Key Results                                               |
|                    | KR1: AI for All member in department                      |
|                    | Progress: 0%   Start: 0   Target: 100                      |
+----------------------------------------------------------------------------------+
```

```
+----------------------------------------------------------------------------------+
| Objective Title:                                                                 |
| 1. POC AI for SQL Injection ...                                                 |

| [REPORT] [OPTIONS]                                                                 |
| ---------------------------------------------------------------------------------- |
| Tabs: [General Info] [Conversation] [Grade & Feedback]                             |
| ---------------------------------------------------------------------------------- |
| OKR Overview                                                                       |
| Progress: Not reported yet                                                         |
| Owner: Nguyen Van A                                                            |
| Update due: 30-Jun-2026                                                            |
| ---------------------------------------------------------------------------------- |
| Key Results                                                                        |
| ---------------------------------------------------------------------------------- |
| KR1: AI for All member in department                                                       |
| Progress: 0%        Start: 0    Target: 100                                        |
| Deadline: 30-Jun-2026                                                              |
| ---------------------------------------------------------------------------------- |

```

---

### SCR-03: Create / Edit Objective
| Item | Nội dung |
|------|---------|
| Input | Title, Description, Owner, Time period |
| Action | Save |

### UI Mockup
```

+----------------------------------------------------------------------------------+
| FOKR | [All FPT v]   [Search.....................]        [NEW OKR] [ENG v] [🔔] |
+----------------------------------------------------------------------------------+

| Sidebar                                                                              | Create Objective                    |
| ------------------------------------------------------------------------------------ | ----------------------------------- |
| 2026                                                                                 | Title: [..........................] |
| My OKRs                                                                              | Description:                        |
| - I created                                                                          | [..............................]    |
| - I manage                                                                           | Owner: [Dropdown]                   |
| Members                                                                              | Quarter: [Q2/2026 v]                |
| OKR - all                                                                            |                                     |
| --------------------                                                                 | [ Save ]                            |
| +----------------------------------------------------------------------------------+ |                                     |
```

```
+--------------------------------------+
| Create Objective                     |
+--------------------------------------+
| Title: [..........................]  |
| Description:                        |
| [..............................]    |
| Owner: [Dropdown]                  |
| Quarter: [Q2/2026 v]               |
|                                    |
|          [ Save ]                  |
+--------------------------------------+
```

---

### SCR-04: Key Result Detail / Update

| Item   | Nội dung              |
| ------ | --------------------- |
| Input  | Progress (%), comment |
| Action | Save                  |

### UI Mockup

```
+----------------------------------------------------------------------------------+
| FOKR | [All FPT v]   [Search.....................]        [NEW OKR] [ENG v] [🔔] |
+----------------------------------------------------------------------------------+
| Sidebar            | Key Result Detail                                          |
|--------------------|------------------------------------------------------------|
| 2026               | KR: Reduce bugs by 30%                                    |
| My OKRs            | Owner: Nguyen Van A                                             |
| - I created        | Deadline: 30-Jun-2026                                     |
| - I manage         |------------------------------------------------------------|
| Members            | Current Progress: 60%                                     |
| OKR - all          | Update Progress: [ 70 ] %                                 |
|--------------------| Comment:                                                  |
|                    | [..............................]                          |
|                    |                    [ Save ]                                |
+----------------------------------------------------------------------------------+
```

```
+--------------------------------------+
| Key Result Detail                    |
+--------------------------------------+
| KR: Reduce bugs by 30%              |
| Owner: Nguyen Van A                       |

| Deadline: 30-Jun-2026                    |
| ---------------------------------------- |
| Current Progress: 60%                    |
| Update Progress: [ 70 ] %                |
| Comment:                                 |
| [..............................]         |
|                                          |
| [ Save ]                                 |
| +--------------------------------------+ |

```

---

## 7. Data Definition

### Objective
| Field | Type | Description |
|------|------|------------|
| id | int | ID |
| title | string | Tên Objective |
| description | string | Mô tả |
| owner_id | int | Người tạo |
| quarter | string | Kỳ OKR |
| status | string | trạng thái |

### Key Result
| Field | Type | Description |
|------|------|------------|
| id | int | ID |
| objective_id | int | Liên kết Objective |
| title | string | Tên KR |
| progress | number | % tiến độ |
| start_value | number | Giá trị bắt đầu |
| target_value | number | Mục tiêu |
| deadline | date | Hạn |

### User
| Field | Type | Description |
|------|------|------------|
| id | int | ID |
| name | string | Tên |
| role | string | Vai trò |


### Objective
| Field | Type | Description |
|------|------|------------|
| id | int | ID |
| title | string | Tên Objective |
| owner | user | Người tạo |

### Key Result
| Field | Type | Description |
|------|------|------------|
| id | int | ID |
| objective_id | int | Liên kết Objective |
| progress | number | % tiến độ |


### Objective
| Field | Type | Description |
|------|------|------------|
| id | int | ID |
| title | string | Tên Objective |
| owner | user | Người tạo |

### Key Result
| Field | Type | Description |
|------|------|------------|
| id | int | ID |
| objective_id | int | Liên kết Objective |
| progress | number | % tiến độ |

---

## 8. Non-functional Requirements

### 8.1 Performance
- Response < 2s

### 8.2 Security
- Authentication required

---

## 9. Constraints
- Web-based system

---

## 10. Assumptions
- Workshop purpose only (không production-ready)
