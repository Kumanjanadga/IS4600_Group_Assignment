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
| `TestCaseDocument_Group20.pdf` | **Print this** – black and white, A4 landscape, no cover page, Group No: 20 on page 1 and in every footer; grouped by member, then module; ends with the defect list (built by `build_pdf.py`) |
| `TestCaseDocument_Group20_v0.1.xlsx` | **Submission file** – Summary, Module Division, Defect Log and all 180 test cases, all grouped by member → module (Template sheet) |
| `DEFECT_REPORT.md` | The 15 defects: steps, expected vs actual, SRS sentence broken, owner |
| `members.json` | Group number, member names/IDs, module split, test case → defect IDs – edit, then rebuild the Excel |
| `test_index.json` | Portal and module of every test case (drives the Excel grouping) |
| `api-tests/tests_m1_…py` … `tests_m6_…py` | Executable API test cases, one file per member (15 each) |
| `api-tests/framework.py`, `client.py`, `helpers.py`, `run_tests.py` | Test runner, HTTP client, fixtures, `parallel()` helper |
| `ui-tests/ui_test_cases.py` | UI test cases written from the SRS (no UI in this release → *Not Executed*), 15 per member |
| `results/api_results.json` | Latest API run (status + actual result per test) |
| `build_excel.py` | Builds the Excel document from the template + results |
| `template/` | Sir's blank test case template (used by `build_excel.py`) |
| `assignment/` | Sir's files: Task 1 instructions, SRS v2.1, Deployment Guide, `qa-training-app.jar`, `application.yml` |

```
qa-project/
├── TestCaseDocument_Group20.pdf        ← print this (the hand-in)
├── TestCaseDocument_Group20_v0.1.xlsx   ← same content as an editable spreadsheet
├── DEFECT_REPORT.md                     ← 15 defects
├── README.md · members.json · build_excel.py
├── api-tests/      90 API test cases (tests_m1 … tests_m6) + runner
├── ui-tests/       90 UI test cases
├── results/        api_results.json (latest run)
├── template/       blank course template
└── assignment/     sir's PDFs, jar and application.yml
```

## Module division (equal weight, ~27 SRS rules each)

Test case IDs read **Portal-Module-Type-Number**: `ADM-CAT-API-12` = Admin App · Category Management · API case 12.
Portals: `ADM` Admin App, `CLI` Client App, `API` Backend API (general rules).

| Member | Portal · Modules | Test case IDs | API test file | Defects |
|---|---|---|---|---|
| Nimhan R.D.S. (224135V) | Admin App · Dashboard & navigation (6.2), Category Management (6.3) | ADM-DSH-*, ADM-CAT-* | `tests_m1_categories_dashboard.py` | DEF-001, 002, 003 |
| Kahanda M.C. (224098H) | Admin App · Plant Management (6.4) | ADM-PLT-API-01–15, ADM-PLT-UI-* | `tests_m2_plants.py` | DEF-004, 005, 006 |
| Kumanjana D.G.A. (224114G) | Client App · Navigation (7.1), Registration (7.2); Backend API · General API rules (4.5, 4.6) | CLI-NAV-*, CLI-REG-*, API-GEN-* | `tests_m3_registration_general.py` | DEF-007, 008 |
| Sathsara H.W.S (224173J) | Admin App · Plant Management (ADM-PLT-API-16); Client App · Plant Catalog (7.3, 4.8), Plant Details (7.4) | ADM-PLT-API-16, CLI-CTL-*, CLI-DET-* | `tests_m4_catalog.py` | DEF-009, 010 |
| Warnasooriya W.M.E.S (224208A) | Admin App · User Management (6.6); Client App · Buy Plant (7.5), My Purchases (7.6) | ADM-USR-*, CLI-BUY-*, CLI-PUR-* | `tests_m5_purchases_users.py` | DEF-011, 012 |
| Aberathna M.H.A.J.D (224003P) | Admin App · Sales Management (6.5) | ADM-SAL-* | `tests_m6_sales.py` | DEF-013, 014, 015 |

- Each person kept the area they already worked on; the split is balanced by the number of SRS rules, not endpoints.
- Token/role checks (401/403) are written only by the member who owns that endpoint, so no scenario is duplicated.
- Restructured on 22/11/2026: all login/logout cases and the 3 "redirect to login" cases were removed and replaced.
  The old run logs (`results/evidence_M1_api.md`, `evidence_M3_api.md`) were removed because they used the old IDs and
  the removed login cases; they remain in the git history.

## Rules we follow (instructions + sir's notices)

1. Each member: 15 API + 15 UI test cases, only inside their own modules; every case carries the writer's name and ID (Tester column).
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
python run_tests.py M3       # one member's file (M1 Nimhan, M2 Kahanda, M3 Kumanjana, M4 Sathsara, M5 Warnasooriya, M6 Aberathna)
```
Tests create their own uniquely-named data, so they can be re-run on the same database. Set `QA_BASE_URL` for another host.
"Parallel" cases send the same request several times at the same moment (`framework.parallel`); in Postman use the
Collection Runner with several iterations and 0 ms delay.

## Rebuilding the Excel and the PDF

```bash
pip install openpyxl reportlab
python build_excel.py
python build_pdf.py
```

## Latest results (API, 22/11/2026)

**75 Passed, 15 Failed** – every failure is one of the 15 defects (10 need only a single request) (`results/api_results.json`, `DEFECT_REPORT.md`).
UI cases: 90 *Not Executed* (no UI in this release).

| Defect | Tester | Portal · Module | Test case | Summary |
|---|---|---|---|---|
| DEF-001 | Nimhan R.D.S. | Admin · Category Management | ADM-CAT-API-12 | "Café" rejected as a duplicate of category "Cafe" |
| DEF-002 | Nimhan R.D.S. | Admin · Category Management | ADM-CAT-API-13 | Duplicate category names saved (parallel) |
| DEF-003 | Nimhan R.D.S. | Admin · Category Management | ADM-CAT-API-14 | 7-character category name (with emoji) rejected as longer than 10 |
| DEF-004 | Kahanda M.C. | Admin · Plant Management | ADM-PLT-API-13 | "Strasse Fern" rejected as a duplicate of plant "Straße Fern" |
| DEF-005 | Kahanda M.C. | Admin · Plant Management | ADM-PLT-API-14 | Stock becomes negative after a sale is deleted |
| DEF-006 | Kahanda M.C. | Admin · Plant Management | ADM-PLT-API-15 | 20-character plant name (with emoji) rejected as longer than 25 |
| DEF-007 | Kumanjana D.G.A. | Client · Registration | CLI-REG-API-12 | 1-character full name (an emoji) accepted |
| DEF-008 | Kumanjana D.G.A. | Backend API · General rules | API-GEN-API-03 | Some errors are HTML instead of JSON |
| DEF-009 | Sathsara H.W.S | Admin · Plant Management | ADM-PLT-API-16 | Deleting the same plant twice → 500 (parallel) |
| DEF-010 | Sathsara H.W.S | Client · Plant Catalog | CLI-CTL-API-09 | Huge page number → 500 on every list |
| DEF-011 | Warnasooriya W.M.E.S | Admin · User Management | ADM-USR-API-05 | Deactivating the same Client twice → both succeed (parallel) |
| DEF-012 | Warnasooriya W.M.E.S | Client · Buy Plant | CLI-BUY-API-07 | Buy Plant drops the out-of-stock error |
| DEF-013 | Aberathna M.H.A.J.D | Admin · Sales Management | ADM-SAL-API-13 | Deleting the same sale twice → 500 (parallel) |
| DEF-014 | Aberathna M.H.A.J.D | Admin · Sales Management | ADM-SAL-API-14 | `soldTo=9999-12-31` → 500 |
| DEF-015 | Aberathna M.H.A.J.D | Admin · Sales Management | ADM-SAL-API-15 | Sell Plant drops the out-of-stock error |
