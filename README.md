# IS4600 – QA Training App · Task 1: Test Case Design

Group assignment for **IS4600 IT Quality Assurance**: test cases for the QA Training App (plant store, Admin App + Client App + Backend API).

| | |
|---|---|
| Release / deadline | 16/11/2026 → **25/11/2026** |
| Members | 6 → minimum **180** test cases (15 API + 15 UI each) |
| Primary references | `QA_Training_App_SRS_v2.1.pdf` (behaviour), Swagger (API details) |

## Contents

| Path | What it is |
|---|---|
| `TestCaseDocument_<Group>_v0.1.xlsx` | **Submission file** – Summary, Module Division, and all 180 test cases (Template sheet) |
| `members.json` | Group number, member IDs/names, module split, defect IDs – edit, then rebuild the Excel |
| `api-tests/` | Executable API test cases (Python, standard library only), 15 per member |
| `ui-tests/ui_test_cases.py` | UI test cases written from the SRS (no UI in this release → *Not Executed*) |
| `results/api_results.json` | Latest API run (status + actual result per test) |
| `build_excel.py` | Builds the Excel document from the template + results |
| `template/` | The original course template |

## Module division

| Member | SRS modules | API endpoints | UI pages |
|---|---|---|---|
| M1 – 224135V Nimhan R.D.S. | Admin login/logout, Category Management | `/api/admin/auth/*`, `/api/admin/categories/*` | `/admin/login`, `/admin/categories`, add/edit |
| M2 – 224098H Kahanda M.C. | Plant Management, Dashboard | `/api/admin/plants/*`, `/api/admin/dashboard/summary` | `/admin/plants`, add/edit, `/admin/dashboard` |
| M3 – 224114G Kumanjana D.G.A. | Registration, Client login | `/api/client/public/auth/register`, `/login` | `/client/register`, `/client/login` |
| M4 – 224173 Sathsara | Catalog, Plant details, list rules | `/api/client/public/plants/*`, `/categories` | `/client/plants`, `/client/plants/{id}`, header |
| M5 – 224208A Warnasooriya W.M.E.S. | Buy Plant, My Purchases, account/session | `/api/client/purchases`, `/plants/{id}/buy-info`, `/me`, `/auth/logout` | `/client/plants/{id}/buy`, `/client/purchases` |
| M6 – 224003P Aberathna M.H.A.J.D. | Sales and User Management | `/api/admin/sales/*`, `/api/admin/users/*` | `/admin/sales`, `/admin/sales/new`, `/admin/users` |

Cross-cutting checks (401/403, wrong-app login, deactivated tokens) are written only by the member who owns that endpoint/page, so no scenario is duplicated.

## Rules we follow (from the instructions + SRS)

1. Each member: ≥15 API + ≥15 UI test cases; every test case carries the author's member ID (Tester column).
2. API test cases state endpoint, HTTP method, role/token, request data, expected status code and response.
3. UI test cases state page URL, role (or Guest), steps, test data and expected result with the **exact SRS message**.
4. Expected results come from the SRS, never from what the app does – any difference is a defect.
5. Duplicates (same scenario + same data) count once, for whoever wrote it first.
6. Only the port / database settings in `application.yml` may be changed.
7. Marks are individual: every test case is marked one by one. The lecturer hid ~15 bugs; test cases should be designed to find them.

## Submission (from the lecturer's voice notes)

- **Hard copy**: print the test case document on A4 or A3 (whatever fits), **one document per group**.
- **Write the group number** (from the lecturer's group Excel) on it. **No cover page, no binding**: just keep the pages in order.
- **Black & white only**, no colour printing.
- Hand it in **by 4 PM** on the deadline (25/11/2026) and **sign** the submission sheet. **No late submissions.**
- Get the app running early; the deadline will not be extended.

## Running the app

1. MySQL 8 (we use Docker):
   ```sql
   CREATE DATABASE qa_training_app;
   CREATE USER 'qa_user'@'%' IDENTIFIED BY 'Qa@12345';
   GRANT ALL PRIVILEGES ON qa_training_app.* TO 'qa_user'@'%';
   FLUSH PRIVILEGES;
   ```
2. From the folder with `qa-training-app.jar` and `application.yml`: `java -jar qa-training-app.jar` (Java 21+).
3. Check http://localhost:8080/api/health and open http://localhost:8080/swagger-ui.html.

## Running the API tests

```bash
cd api-tests
python run_tests.py          # all 90
python run_tests.py M3       # one member
```
Tests create their own uniquely-named data, so they can be re-run on the same database. Set `QA_BASE_URL` for another host.

## Rebuilding the Excel

```bash
pip install openpyxl
python build_excel.py
```

## Latest results (API)

99 Passed, 1 Failed (100 API test cases) – see `results/api_results.json`.

| Defect | Test | Summary |
|---|---|---|
| DEF-001 | TC_API_M3_07 | A valid 100-character email (`<93 chars>@ex.com`) is rejected with "Please enter a valid email address". The validator caps the part before `@` at 64 characters, which the SRS (7.2: max 100, format name@domain.tld) does not define. |
