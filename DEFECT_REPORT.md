# Defect Report: QA Training App (Group 20, IS4600 Task 1)

| | |
|---|---|
| Application | `qa-training-app.jar` as released by sir (MD5 `9ff41da62db74312065ceed6f2de3315`) |
| Environment | Java 25, MySQL 8.4, `http://localhost:8080`, default `application.yml` |
| Reference | `QA_Training_App_SRS_v2.1.pdf` (expected behaviour), Swagger (requests/responses) |
| Date | 22/11/2026 |
| Result | **15 defects, 2-3 per member**, each breaks a sentence the SRS states and is covered by one API test case that fails |

Test case IDs read as **Portal-Module-Type-Number**, e.g. `ADM-CAT-API-12` = Admin App, Category Management, API case 12.
Portals: `ADM` Admin App, `CLI` Client App, `API` Backend API (general rules).

How to reproduce:
- **Single** = one normal request (Swagger, Postman, or `python run_tests.py` in `api-tests/`). 10 of the 15.
- **Parallel** = the same request sent several times at the same moment: Postman **Collection Runner** with N iterations and
  0 ms delay, or our script (`framework.parallel`). 5 of the 15. One-at-a-time requests never show these defects.

## Summary by member

| Defect | Portal · Module | Test case | Defect | Type | Owner | SRS sentence broken |
|---|---|---|---|---|---|---|
| DEF-001 | Admin App · Category Management | ADM-CAT-API-12 | "Café" is rejected as a duplicate of category "Cafe" | Single | Nimhan R.D.S. (224135V) | 6.3.2 "Category names must be unique within the same parent (case-insensitive)" |
| DEF-002 | Admin App · Category Management | ADM-CAT-API-13 | Duplicate category names saved when requests arrive together | Parallel | Nimhan R.D.S. (224135V) | 6.3.2 "Category names must be unique within the same parent" |
| DEF-003 | Admin App · Category Management | ADM-CAT-API-14 | A 7-character category name with emoji is rejected as longer than 10 | Single | Nimhan R.D.S. (224135V) | 6.3.2 "Category Name - Length 3-10" |
| DEF-004 | Admin App · Plant Management | ADM-PLT-API-13 | "Strasse Fern" is rejected as a duplicate of plant "Straße Fern" | Single | Kahanda M.C. (224098H) | 6.4.2 "Plant names must be unique (case-insensitive)" |
| DEF-005 | Admin App · Plant Management | ADM-PLT-API-14 | Stock becomes negative (-2147483644) after a sale is deleted | Single | Kahanda M.C. (224098H) | 6.5.2 "stock can never become negative" |
| DEF-006 | Admin App · Plant Management | ADM-PLT-API-15 | A 20-character plant name with emoji is rejected as longer than 25 | Single | Kahanda M.C. (224098H) | 6.4.2 "Name - Length 3-25" |
| DEF-007 | Client App · Registration | CLI-REG-API-12 | A 1-character full name (an emoji) is accepted | Single | Kumanjana D.G.A. (224114G) | 7.2 "Full Name - Length 2-50" |
| DEF-008 | Backend API · General API rules | API-GEN-API-03 | Some errors are HTML / an empty body instead of the JSON format | Single | Kumanjana D.G.A. (224114G) | 4.5 "Every API response, successful or not, has the same structure" |
| DEF-009 | Admin App · Plant Management | ADM-PLT-API-16 | Deleting the same plant twice at once → 500 | Parallel | Sathsara H.W.S (224173J) | 4.6 404 "Plant not found" when the record does not exist |
| DEF-010 | Client App · Plant Catalog | CLI-CTL-API-09 | A very large page number → 500 on every list | Single | Sathsara H.W.S (224173J) | 4.8 "Requesting a page after the last page returns an empty list" |
| DEF-011 | Admin App · User Management | ADM-USR-API-05 | Deactivating the same Client twice at once → both "successful" | Parallel | Warnasooriya W.M.E.S (224208A) | 6.6.2 "Deactivating a user who is already Inactive is rejected" |
| DEF-012 | Client App · Buy Plant | CLI-BUY-API-07 | Buy Plant drops the out-of-stock error when quantity is also invalid | Single | Warnasooriya W.M.E.S (224208A) | 4.7 "one message per field" + 7.5 field table |
| DEF-013 | Admin App · Sales Management | ADM-SAL-API-13 | Deleting the same sale twice at once → 500 | Parallel | Aberathna M.H.A.J.D (224003P) | 4.6 404 "Sale not found" when the record does not exist |
| DEF-014 | Admin App · Sales Management | ADM-SAL-API-14 | Sold-date filter `soldTo=9999-12-31` → 500 | Single | Aberathna M.H.A.J.D (224003P) | 6.5.1 "filtered by sold date, using a From date and a To date (both inclusive)" |
| DEF-015 | Admin App · Sales Management | ADM-SAL-API-15 | Sell Plant drops the out-of-stock error when quantity is also invalid | Single | Aberathna M.H.A.J.D (224003P) | 4.7 "Validation errors return one message per field" + 6.5.2 field table |

Per member: Nimhan 3, Kahanda 3, Kumanjana 2, Sathsara 2, Warnasooriya 2, Aberathna 3. Modules with no defects: Dashboard & navigation, Navigation, Plant Details, My Purchases.

Root causes (for the developers): DEF-001/004 the database compares names accent-insensitively (MySQL collation
`utf8mb4_0900_ai_ci`); DEF-003/006/007 lengths are counted in UTF-16 code units, so an emoji counts as 2; DEF-002/011
no locking for simultaneous requests; DEF-009/013 a second delete of the same record is not caught (500);
DEF-012/015 existence/stock rules run only after the other fields are valid.

---

# Nimhan R.D.S. (224135V)

## Admin App · Category Management (SRS 6.3)

### DEF-001 "Café" rejected as a duplicate category · Single · ADM-CAT-API-12 · Nimhan R.D.S.
- **Steps:** Admin token. 1) `POST /api/admin/categories` `{"name":"Cafe","parentId":null}` → 201.
  2) `POST /api/admin/categories` `{"name":"Café","parentId":null}`.
- **Expected:** 201 "Category created successfully" - names are unique only ignoring letter case; "Café" is a different name.
- **Actual:** **409 `errors.name` = "Category name already exists"**. Same for Straße/Strasse, Résumé/Resume, Über/Uber,
  Æon/Aeon, and on `PUT` (rename).

### DEF-002 Duplicate category names saved together · Parallel · ADM-CAT-API-13 · Nimhan R.D.S.
- **Steps:** Send 8 × `POST /api/admin/categories` `{"name":"DupTest","parentId":null}` at the same moment.
- **Expected:** one 201, the rest 409 "Category name already exists".
- **Actual:** 5-8 × 201; `GET /api/admin/categories?search=DupTest` lists 5-8 categories with the same name and the Dashboard
  counts them all. One at a time, the 2nd request is correctly 409. (Plants, usernames and emails are not affected.)

### DEF-003 7-character category name rejected · Single · ADM-CAT-API-14 · Nimhan R.D.S.
- **Steps:** `POST /api/admin/categories` `{"name":"Abc🌵🌵🌵🌵","parentId":null}` (7 characters).
- **Expected:** 201 (3-10 characters).
- **Actual:** **400 "Category name must be between 3 and 10 characters"**. Six cactus emoji (6 characters) are also rejected,
  while five are accepted: each emoji is counted as 2.

# Kahanda M.C. (224098H)

## Admin App · Plant Management (SRS 6.4)

### DEF-004 "Strasse Fern" rejected as a duplicate plant · Single · ADM-PLT-API-13 · Kahanda M.C.
- **Steps:** Admin token, a sub-category S. 1) `POST /api/admin/plants` `{"name":"Straße Fern","categoryId":<S>,"price":5,"quantity":5}`.
  2) `POST /api/admin/plants` `{"name":"Strasse Fern","categoryId":<S>,"price":5,"quantity":5}`.
- **Expected:** 201 "Plant created successfully" (unique only ignoring letter case).
- **Actual:** **409 `errors.name` = "Plant name already exists"**. Same for Cafe/Café, Uber/Über and on `PUT /api/admin/plants/{id}`.

### DEF-005 Negative stock · Single · ADM-PLT-API-14 · Kahanda M.C.
- **Steps:** 1) plant with quantity 10; 2) `POST /api/admin/sales` quantity 5; 3) `PUT /api/admin/plants/{id}` with
  `"quantity": 2147483647` (accepted: the SRS sets no maximum); 4) `DELETE /api/admin/sales/{saleId}`.
- **Expected:** stock is never negative.
- **Actual:** 200 "Sale deleted successfully"; quantity becomes **-2147483644**. The plant is now "Out of Stock", flagged Low,
  and can't be sold. The same happens when a Client purchase is deleted.

### DEF-006 20-character plant name rejected · Single · ADM-PLT-API-15 · Kahanda M.C.
- **Steps:** `POST /api/admin/plants` `{"name":"RoseAbcd🌹🌹🌹🌹🌹🌹🌹🌹🌹🌹🌹🌹","categoryId":<S>,"price":5,"quantity":1}` (20 characters).
- **Expected:** 201 (3-25 characters).
- **Actual:** **400 "Plant name must be between 3 and 25 characters"** (each emoji counted as 2).

# Kumanjana D.G.A. (224114G)

## Client App · Registration (SRS 7.2)

### DEF-007 1-character full name accepted · Single · CLI-REG-API-12 · Kumanjana D.G.A.
- **Steps:** `POST /api/client/public/auth/register` with a valid body and `"fullName":"😀"`.
- **Expected:** 400 `errors.fullName` = "Full name must be between 2 and 50 characters".
- **Actual:** **201 "Registration successful. Please log in."** The reverse also fails: a full name of 26 emoji (26 characters)
  is rejected as longer than 50, and a 13-character password with emoji is rejected as longer than 20.

## Backend API · General API rules (SRS 4.5, 4.6)

### DEF-008 Non-JSON error responses · Single · API-GEN-API-03 · Kumanjana D.G.A.
- **Steps / actual:**
  - `GET /api/client/public/plants?search=<9000 × "a">` → 400 **HTML** page "HTTP Status 400 – Bad Request"
  - a request with a 20 KB header, or a space in the URL path → 400 HTML
  - `GET /api/client/public/plants` with header `Accept: text/html` → 406 **"Whitelabel Error Page"** HTML
  - `TRACE /api/client/public/plants` → 400 with an **empty body**
- **Expected:** `{"success":false,"message":...}` for every response (4.5); unsupported method → 405
  "Method TRACE is not supported for this endpoint" (4.6).

---

# Sathsara H.W.S (224173J)

## Admin App · Plant Management (SRS 6.4)

### DEF-009 Same plant deleted twice at once → 500 · Parallel · ADM-PLT-API-16 · Sathsara H.W.S
- **Steps:** a plant without sales. Send 5 × `DELETE /api/admin/plants/{id}` at the same moment.
- **Expected:** one 200 "Plant deleted successfully", others 404 "Plant not found".
- **Actual:** others **500 `{"success":false,"message":"Unexpected server error"}`**. (Categories behave the same.)

## Client App · Plant Catalog (SRS 7.3, 4.8)

### DEF-010 Huge page number → 500 · Single · CLI-CTL-API-09 · Sathsara H.W.S
- **Steps:** `GET /api/client/public/plants?page=2147483647&size=10` (no token). Also `/api/admin/plants`, `/sales`, `/users`,
  `/categories` and `/api/client/purchases`.
- **Expected:** 200 with an empty list.
- **Actual:** **500 "Unexpected server error"** whenever (page − 1) × size is above ~2.1 billion
  (`page=214748365&size=10` → 200, `page=2147483647&size=10` → 500).

# Warnasooriya W.M.E.S (224208A)

## Admin App · User Management (SRS 6.6)

### DEF-011 Deactivate the same Client twice at once · Parallel · ADM-USR-API-05 · Warnasooriya W.M.E.S
- **Steps:** an active Client. Send 6 × `PATCH /api/admin/users/{id}/deactivate` at the same moment (same with `/activate`).
- **Expected:** one 200 "User deactivated successfully.", others 409 "User is already inactive".
- **Actual:** 5-6 × 200 "User deactivated successfully." (6 × 200 for activate).

## Client App · Buy Plant (SRS 7.5)

### DEF-012 Buy Plant: missing out-of-stock error · Single · CLI-BUY-API-07 · Warnasooriya W.M.E.S
- **Steps:** Client token. `POST /api/client/purchases` `{"plantId":<plant with stock 0>,"quantity":0}`.
- **Expected:** `errors.quantity` = "Quantity must be greater than 0" **and** the plant error "This plant is out of stock".
- **Actual:** only `errors.quantity`.
- Note: `{"plantId":999999,"quantity":1.5}` returning only the type error is **correct** (4.7 "If a field has the wrong
  type, only that field's error is returned").

# Aberathna M.H.A.J.D (224003P)

## Admin App · Sales Management (SRS 6.5)

### DEF-013 Same sale deleted twice at once → 500 · Parallel · ADM-SAL-API-13 · Aberathna M.H.A.J.D
- **Steps:** one sale (Admin sale or Client purchase). Send 6 × `DELETE /api/admin/sales/{id}` at the same moment.
- **Expected:** one 200 "Sale deleted successfully", others 404 "Sale not found".
- **Actual:** others **500 "Unexpected server error"** (stock is restored only once, correctly).

### DEF-014 `soldTo=9999-12-31` → 500 · Single · ADM-SAL-API-14 · Aberathna M.H.A.J.D
- **Steps:** `GET /api/admin/sales?soldTo=9999-12-31` (Admin token).
- **Expected:** 200 "Sales retrieved successfully" with all sales sold on or before that date.
- **Actual:** **500 "Unexpected server error"** (`soldTo=9999-12-30` and `soldFrom=9999-12-31` return 200).

### DEF-015 Sell Plant: missing out-of-stock error · Single · ADM-SAL-API-15 · Aberathna M.H.A.J.D
- **Steps:** `POST /api/admin/sales` `{"plantId":<plant with stock 0>,"quantity":0}` (also `{"plantId":999999,"quantity":null}`).
- **Expected:** `errors.quantity` = "Quantity must be greater than 0" **and** the plant error "This plant is out of stock".
- **Actual:** only `errors.quantity`.

---

## Also found (not counted in the 15, to keep 2-3 per member and avoid repeating a root cause)
- Category/plant form drops the "Parent category not found" / "Category not found" error when another field is invalid (4.7).
- Simultaneous requests can make a 3-level category tree, or a main category that holds plants (6.3.2).
- Deleting the same category twice at once → 500 (4.6).

## Observations (the SRS does not define these inputs)
- Names made only of invisible spaces (U+00A0, U+200B) are accepted; `"Indoor"` + U+00A0 makes a look-alike duplicate.
- A duplicated `"quantity"` key in a JSON body → 500; `"quantity": 99999999999` → "Malformed request body".
- With MySQL stopped, `/api/health` correctly reports `"database":"DOWN"`.

## What was checked and found correct
About 400 SRS rules across all modules, all 140+ messages in the jar (word for word), about 110 invalid inputs on every write
endpoint, 51 first-start / restart / configuration checks (Deployment Guide), and in parallel: same username, email and
plant name (also in different letter case), 8 buyers on stock 3, unit price/total during price edits, delete vs.
add/move/sell, login vs. deactivation. Validation order, combined delete messages, partial search, numbers sent as text and
"equal sort values ordered by ID" also match the SRS.
