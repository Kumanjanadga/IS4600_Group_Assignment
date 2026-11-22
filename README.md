# IS4600 – QA Training App · Task 1: Test Case Design (Group 20)

Group assignment for **IS4600 IT Quality Assurance**: test cases for the QA Training App (plant store, Admin App + Client App + Backend API).

| | |
|---|---|
| Release / deadline | 16/11/2026 → **25/11/2026 (Wednesday)** |
| Members | 6 → **180** test cases (15 API + 15 UI each), no login/logout cases |
| Primary references | `QA_Training_App_SRS_v2.1.pdf` (behaviour), Swagger (API details) |
| Defects found | **15** – see [`DEFECT_REPORT.md`](DEFECT_REPORT.md) |

## Contents

| Path | What it is |
|---|---|
| `TestCaseDocument_Group20_v0.1.xlsx` | **Submission file** – Summary, Module Division, Defect Log and all 180 test cases (Template sheet) |
| `DEFECT_REPORT.md` | The 15 defects: steps, expected vs actual, SRS sentence broken, owner |
| `members.json` | Group number, member IDs/names, module split, test case → defect IDs – edit, then rebuild the Excel |
| `api-tests/tests_m1_…py` … `tests_m6_…py` | Executable API test cases, one file per member (15 each) |
| `api-tests/framework.py`, `client.py`, `helpers.py`, `run_tests.py` | Test runner, HTTP client, fixtures, `parallel()` helper |
| `ui-tests/ui_test_cases.py` | UI test cases written from the SRS (no UI in this release → *Not Executed*), 15 per member |
| `results/api_results.json` | Latest API run (status + actual result per test) |
| `build_excel.py` | Builds the Excel document from the template + results |
| `template/` | Sir's blank test case template (used by `build_excel.py`) |
| `assignment/` | Sir's files: Task 1 instructions, SRS v2.1, Deployment Guide, `qa-training-app.jar`, `application.yml` |

```
qa-project/
├── TestCaseDocument_Group20_v0.1.xlsx   ← print this (the submission)
├── DEFECT_REPORT.md                     ← 15 defects
├── README.md · members.json · build_excel.py
├── api-tests/      90 API test cases (tests_m1 … tests_m6) + runner
├── ui-tests/       90 UI test cases
├── results/        api_results.json (latest run)
├── template/       blank course template
└── assignment/     sir's PDFs, jar and application.yml
```

## Module division (equal weight, ~27 SRS rules each)

| Member | SRS modules | API test file / endpoints | UI pages | Defects |
|---|---|---|---|---|
| M1 – 224135V Nimhan R.D.S. | Category Management (6.3) + Dashboard (6.2) | `tests_m1_categories_dashboard.py` · `/api/admin/categories/*`, `/api/admin/dashboard/summary` | `/admin/categories`, add/edit, `/admin/dashboard` | DEF-001, 002, 003 |
| M2 – 224098H Kahanda M.C. | Plant Management (6.4) | `tests_m2_plants.py` · `/api/admin/plants/*` | `/admin/plants`, add/edit | DEF-004, 005, 006 |
| M3 – 224114G Kumanjana D.G.A. | Registration (7.2) + Navigation/header (7.1) + general API rules (4.5, 4.6) | `tests_m3_registration_general.py` · `/api/client/public/auth/register`, 405/415/response format | `/client/register`, `/client`, header | DEF-007, 008 |
| M4 – 224173 Sathsara | Plant Catalog + Plant Details (7.3, 7.4) + list rules (4.8) | `tests_m4_catalog.py` · `/api/client/public/plants/*`, `/api/client/public/categories`, page/size/sort | `/client/plants`, `/client/plants/{id}` | DEF-009, 010 |
| M5 – 224208A Warnasooriya W.M.E.S. | Buy Plant + My Purchases (7.5, 7.6) + User Management (6.6) | `tests_m5_purchases_users.py` · `/api/client/purchases`, `/plants/{id}/buy-info`, `/api/admin/users/*` | `/client/plants/{id}/buy`, `/client/purchases`, `/admin/users` | DEF-011, 012 |
| M6 – 224003P Aberathna M.H.A.J.D. | Sales Management + Sell Plant (6.5) | `tests_m6_sales.py` · `/api/admin/sales/*` | `/admin/sales`, `/admin/sales/new` | DEF-013, 014, 015 |

- Each person kept the area they already worked on; the split is balanced by the number of SRS rules, not endpoints.
- Token/role checks (401/403) are written only by the member who owns that endpoint, so no scenario is duplicated.
- Restructured on 22/11/2026: all login/logout cases and the 3 "redirect to login" cases were removed and replaced.
  The old run logs (`results/evidence_M1_api.md`, `evidence_M3_api.md`) were removed because they used the old IDs and
  the removed login cases; they remain in the git history.

## Rules we follow (instructions + sir's notices)

1. Each member: 15 API + 15 UI test cases, only inside their own modules; every case carries the writer's ID (Tester column).
2. **No test cases for the login function** (login page, login API, logout) – sir's notice.
3. API cases state endpoint, HTTP method, role/token, request data, expected status code and response.
4. UI cases state page URL, role (or Guest), steps, test data and the expected result with the **exact SRS message**.
5. Expected results come from the SRS, never from what the app does – any difference is a defect.
6. No duplicates: the same scenario with the same data counts once, for whoever wrote it first. Marks are individual.
7. Only the port / database settings in `application.yml` may be changed.
8. Sir hid ~15 bugs; find at least 12 (about 2 per member). Our 15 are in `DEFECT_REPORT.md`.

## Submission

- **One printed document per group**, A4 or A3, **black & white only** (colour loses marks).
- Write the **group number (20)** on it. **No cover page, no binding – staple it.**
- Hand it in to the department by **25/11/2026 (Wednesday)**, 4 PM; earlier is fine. No late submissions.

## Running the app

1. MySQL 8 (we use Docker):
   ```sql
   CREATE DATABASE qa_training_app;
   CREATE USER 'qa_user'@'%' IDENTIFIED BY 'Qa@12345';
   GRANT ALL PRIVILEGES ON qa_training_app.* TO 'qa_user'@'%';
   FLUSH PRIVILEGES;
   ```
2. From the `assignment/` folder (it holds `qa-training-app.jar` and `application.yml`): `cd assignment` then `java -jar qa-training-app.jar` (Java 21+).
3. Check http://localhost:8080/api/health and open http://localhost:8080/swagger-ui.html.

## Running the API tests

```bash
cd api-tests
python run_tests.py          # all 90
python run_tests.py M3       # one member
```
Tests create their own uniquely-named data, so they can be re-run on the same database. Set `QA_BASE_URL` for another host.
"Parallel" cases send the same request several times at the same moment (`framework.parallel`); in Postman use the
Collection Runner with several iterations and 0 ms delay.

## Rebuilding the Excel

```bash
pip install openpyxl
python build_excel.py
```

## Latest results (API, 22/11/2026)

**75 Passed, 15 Failed** – every failure is one of the 15 defects (10 need only a single request) (`results/api_results.json`, `DEFECT_REPORT.md`).
UI cases: 90 *Not Executed* (no UI in this release).

| Defect | Test case | Summary |
|---|---|---|
| DEF-001 | TC_API_M1_13 | "Café" rejected as a duplicate of category "Cafe" |
| DEF-002 | TC_API_M1_15 | 7-character category name (with emoji) rejected as longer than 10 |
| DEF-003 | TC_API_M1_14 | Duplicate category names saved (parallel) |
| DEF-004 | TC_API_M2_14 | Stock becomes negative after a sale is deleted |
| DEF-005 | TC_API_M2_13 | "Strasse Fern" rejected as a duplicate of plant "Straße Fern" |
| DEF-006 | TC_API_M2_15 | 20-character plant name (with emoji) rejected as longer than 25 |
| DEF-007 | TC_API_M3_14 | 1-character full name (an emoji) accepted |
| DEF-008 | TC_API_M3_15 | Some errors are HTML instead of JSON |
| DEF-009 | TC_API_M4_14 | Huge page number → 500 on every list |
| DEF-010 | TC_API_M4_15 | Deleting the same plant twice → 500 (parallel) |
| DEF-011 | TC_API_M5_14 | Deactivating the same Client twice → both succeed (parallel) |
| DEF-012 | TC_API_M5_15 | Buy Plant drops the out-of-stock error |
| DEF-013 | TC_API_M6_14 | `soldTo=9999-12-31` → 500 |
| DEF-014 | TC_API_M6_15 | Sell Plant drops the out-of-stock error |
| DEF-015 | TC_API_M6_13 | Deleting the same sale twice → 500 (parallel) |
