# Defect Report: QA Training App (Group 20, IS4600 Task 1)

| | |
|---|---|
| Application | `qa-training-app.jar` as released by sir (MD5 `9ff41da62db74312065ceed6f2de3315`) |
| Environment | Java 25, MySQL 8.4, `http://localhost:8080`, default `application.yml` |
| Reference | `QA_Training_App_SRS_v2.1.pdf` (expected behaviour), Swagger (requests/responses) |
| Date | 22/11/2026 |
| Result | **15 defects**, each breaks a sentence the SRS states; each is covered by one API test case that fails |

How to reproduce:
- **Single** = one normal request (Swagger, Postman or `python run_tests.py <M#>` in `api-tests/`).
- **Parallel** = the same request sent several times at the same moment: Postman **Collection Runner** with N iterations and
  0 ms delay, or our script (`framework.parallel`). Sequential requests never show these defects.

## Summary

| Defect | Test case | Owner | Defect | Type | SRS sentence broken |
|---|---|---|---|---|---|
| DEF-001 | TC_API_M1_14 | M1 Nimhan R.D.S. (224135V) | Duplicate category names saved under the same parent | Parallel | 6.3.2 "Category names must be unique within the same parent" |
| DEF-002 | TC_API_M1_15 | M1 Nimhan R.D.S. (224135V) | A category ends up with a parent AND children (3 levels) | Parallel | 6.3.2 "Categories have two levels only" |
| DEF-003 | TC_API_M1_13 | M1 Nimhan R.D.S. (224135V) | Category form drops the parent error when the name is also invalid | Single | 4.7 "Validation errors return one message per field" |
| DEF-004 | TC_API_M2_13 | M2 Kahanda M.C. (224098H) | A main category ends up holding plants; those plants can't be edited any more | Parallel | 6.3.2 "A sub-category that has plants cannot be changed into a main category" |
| DEF-005 | TC_API_M2_14 | M2 Kahanda M.C. (224098H) | Stock becomes negative (-2147483644) after a sale is deleted | Single | 6.5.2 "stock can never become negative" |
| DEF-006 | TC_API_M2_15 | M2 Kahanda M.C. (224098H) | Plant form drops the category error when another field is also invalid | Single | 4.7 "one message per field" |
| DEF-007 | TC_API_M6_13 | M6 Aberathna M.H.A.J.D. (224003P) | Deleting the same sale twice at once → 500 | Parallel | 4.6 404 "Sale not found" when the record does not exist |
| DEF-008 | TC_API_M6_14 | M6 Aberathna M.H.A.J.D. (224003P) | Sold-date filter `soldTo=9999-12-31` → 500 | Single | 6.5.1 "filtered by sold date, using a From date and a To date (both inclusive)" |
| DEF-009 | TC_API_M6_15 | M6 Aberathna M.H.A.J.D. (224003P) | Sell Plant drops the out-of-stock error when quantity is also invalid | Single | 4.7 + 6.5.2 field table |
| DEF-010 | TC_API_M3_14 | M3 Kumanjana D.G.A. (224114G) | Deleting the same category twice at once → 500 | Parallel | 4.6 404 "Category not found" |
| DEF-011 | TC_API_M3_15 | M3 Kumanjana D.G.A. (224114G) | Some errors are HTML / an empty body instead of the JSON format | Single | 4.5 "Every API response, successful or not, has the same structure" |
| DEF-012 | TC_API_M4_14 | M4 Sathsara (224173) | A very large page number → 500 on every list | Single | 4.8 "Requesting a page after the last page returns an empty list" |
| DEF-013 | TC_API_M4_15 | M4 Sathsara (224173) | Deleting the same plant twice at once → 500 | Parallel | 4.6 404 "Plant not found" |
| DEF-014 | TC_API_M5_14 | M5 Warnasooriya W.M.E.S. (224208A) | Deactivating the same Client twice at once → both "successful" | Parallel | 6.6.2 "Deactivating a user who is already Inactive is rejected" |
| DEF-015 | TC_API_M5_15 | M5 Warnasooriya W.M.E.S. (224208A) | Buy Plant drops the out-of-stock error when quantity is also invalid | Single | 4.7 + 7.5 field table |

Each member owns 2-3 defects (M1 3, M2 3, M6 3, M3 2, M4 2, M5 2). Registration and the Plant Catalog had no
defects of their own, so M3 and M4 own the general-rule defects (SRS 4.5, 4.6, 4.8).

---

## DEF-001 Duplicate category names (Parallel) · TC_API_M1_14 · M1
- **Steps:** Admin token. Send 8 × `POST /api/admin/categories` `{"name":"DupTest","parentId":null}` at the same moment
  (also happens for a sub-category, and for two `PUT` renames of different categories to the same name).
- **Expected:** one 201 "Category created successfully", the rest 409 "Category name already exists".
- **Actual:** 5-8 × 201; `GET /api/admin/categories?search=DupTest` lists 5-8 categories with the same name and the
  Dashboard counts them all. One at a time, the 2nd request is correctly 409. (Plant names, usernames and emails, even in
  different letter case, are NOT affected.)

## DEF-002 Three-level category tree (Parallel) · TC_API_M1_15 · M1
- **Steps:** main categories M and O. At the same moment: `PUT /api/admin/categories/{M}` `{"name":"<M>","parentId":<O>}`
  and 2 × `POST /api/admin/categories` `{"name":"<new>","parentId":<M>}`.
- **Expected:** the move ("A category with sub-categories cannot be moved under another category") or the new
  sub-categories ("Parent category must be a main category") are rejected.
- **Actual:** all succeed → O > M > child. A plant can be added to the child (201); that category is not listed in the
  catalog filter and filtering the catalog by O shows 0 plants.

## DEF-003 Category form: missing parent error (Single) · TC_API_M1_13 · M1
- **Steps:** `POST /api/admin/categories` `{"name":"AB","parentId":999999}` (same on `PUT /api/admin/categories/{id}`,
  and with `{"name":"","parentId":<a sub-category id>}`).
- **Expected:** `errors.name` = "Category name must be between 3 and 10 characters" **and** `errors.parentId` = "Parent category not found".
- **Actual:** only `errors.name`; the parent error appears only after the name is fixed.

## DEF-004 Main category holding plants (Parallel) · TC_API_M2_13 · M2
- **Steps:** sub-category S without plants. At the same moment: `PUT /api/admin/categories/{S}` `{"name":"<S>","parentId":null}`
  and 3 × `POST /api/admin/plants` `{"name":"<new>","categoryId":<S>,"price":5,"quantity":7}`.
- **Expected:** one side is rejected ("A category with plants must stay a sub-category" / "Category must be a sub-category").
- **Actual:** all succeed: S is a main category with plants. The catalog shows the category as `"S"` instead of
  `"Parent Category > Sub-category"` (7.4), and `PUT /api/admin/plants/{id}` with the same category now fails with
  "Category must be a sub-category", so those plants can't be edited.

## DEF-005 Negative stock (Single) · TC_API_M2_14 · M2
- **Steps:** 1) plant with quantity 10; 2) `POST /api/admin/sales` quantity 5; 3) `PUT /api/admin/plants/{id}` with
  `"quantity": 2147483647` (accepted: the SRS sets no maximum); 4) `DELETE /api/admin/sales/{saleId}`.
- **Expected:** stock is never negative.
- **Actual:** 200 "Sale deleted successfully"; quantity becomes **-2147483644**. The plant is now "Out of Stock", flagged
  Low, and can't be sold. The same happens when a Client purchase is deleted.

## DEF-006 Plant form: missing category error (Single) · TC_API_M2_15 · M2
- **Steps:** `POST /api/admin/plants` `{"name":"Okay Plant","categoryId":999999,"price":0,"quantity":1}`
  (also `{"name":"AB","categoryId":<main id>,...}` and the same on `PUT /api/admin/plants/{id}`).
- **Expected:** `errors.price` = "Price must be greater than 0" **and** `errors.categoryId` = "Category not found".
- **Actual:** only `errors.price`.

## DEF-007 Same sale deleted twice at once → 500 (Parallel) · TC_API_M6_13 · M6
- **Steps:** one sale (Admin sale or Client purchase). Send 6 × `DELETE /api/admin/sales/{id}` at the same moment.
- **Expected:** one 200 "Sale deleted successfully", others 404 "Sale not found".
- **Actual:** others **500 `{"success":false,"message":"Unexpected server error"}`** (stock is restored only once, correctly).

## DEF-008 `soldTo=9999-12-31` → 500 (Single) · TC_API_M6_14 · M6
- **Steps:** `GET /api/admin/sales?soldTo=9999-12-31` (Admin token).
- **Expected:** 200 "Sales retrieved successfully" with all sales sold on or before that date.
- **Actual:** **500 "Unexpected server error"** (`soldTo=9999-12-30` and `soldFrom=9999-12-31` return 200).

## DEF-009 Sell Plant: missing out-of-stock error (Single) · TC_API_M6_15 · M6
- **Steps:** `POST /api/admin/sales` `{"plantId":<plant with stock 0>,"quantity":0}` (also `{"plantId":999999,"quantity":null}`).
- **Expected:** `errors.quantity` = "Quantity must be greater than 0" **and** the plant error "This plant is out of stock".
- **Actual:** only `errors.quantity`.

## DEF-010 Same category deleted twice at once → 500 (Parallel) · TC_API_M3_14 · M3
- **Steps:** an empty main category. Send 5 × `DELETE /api/admin/categories/{id}` at the same moment.
- **Expected:** one 200 "Category deleted successfully", others 404 "Category not found".
- **Actual:** others **500 "Unexpected server error"**.

## DEF-011 Non-JSON error responses (Single) · TC_API_M3_15 · M3
- **Steps / actual:**
  - `GET /api/client/public/plants?search=<9000 × "a">` → 400 **HTML** page "HTTP Status 400 – Bad Request"
  - a request with a 20 KB header, or a space in the URL path → 400 HTML
  - `GET /api/client/public/plants` with header `Accept: text/html` → 406 **"Whitelabel Error Page"** HTML
  - `TRACE /api/client/public/plants` → 400 with an **empty body**
- **Expected:** `{"success":false,"message":...}` for every response (4.5); unsupported method → 405
  "Method TRACE is not supported for this endpoint" (4.6).

## DEF-012 Huge page number → 500 (Single) · TC_API_M4_14 · M4
- **Steps:** `GET /api/client/public/plants?page=2147483647&size=10` (no token). Also `/api/admin/plants`, `/sales`,
  `/users`, `/categories` and `/api/client/purchases`.
- **Expected:** 200 with an empty list.
- **Actual:** **500 "Unexpected server error"** whenever (page − 1) × size is above ~2.1 billion
  (`page=214748365&size=10` → 200, `page=2147483647&size=10` → 500).

## DEF-013 Same plant deleted twice at once → 500 (Parallel) · TC_API_M4_15 · M4
- **Steps:** a plant without sales. Send 5 × `DELETE /api/admin/plants/{id}` at the same moment.
- **Expected:** one 200 "Plant deleted successfully", others 404 "Plant not found".
- **Actual:** others **500 "Unexpected server error"**.

## DEF-014 Deactivate the same Client twice at once (Parallel) · TC_API_M5_14 · M5
- **Steps:** an active Client. Send 6 × `PATCH /api/admin/users/{id}/deactivate` at the same moment (same with `/activate`).
- **Expected:** one 200 "User deactivated successfully.", others 409 "User is already inactive".
- **Actual:** 5-6 × 200 "User deactivated successfully." (6 × 200 for activate).

## DEF-015 Buy Plant: missing out-of-stock error (Single) · TC_API_M5_15 · M5
- **Steps:** Client token. `POST /api/client/purchases` `{"plantId":<plant with stock 0>,"quantity":0}`.
- **Expected:** `errors.quantity` = "Quantity must be greater than 0" **and** the plant error "This plant is out of stock".
- **Actual:** only `errors.quantity`.
- Note: `{"plantId":999999,"quantity":1.5}` returning only the type error is **correct** (4.7 "If a field has the wrong
  type, only that field's error is returned").

---

## Observations (not counted: the SRS does not define these inputs)
- Names made only of invisible spaces (U+00A0, U+200B) are accepted for categories, plants and full name; `"Indoor"` +
  U+00A0 makes a look-alike duplicate.
- A duplicated `"quantity"` key in a JSON body → 500.
- `"quantity": 99999999999` → "Malformed request body" instead of a field error.
- With MySQL stopped, `/api/health` correctly reports `"database":"DOWN"`.

## What was checked and found correct
About 400 SRS rules across all modules, all 140+ messages in the jar (word for word), about 110 invalid inputs on every
write endpoint, 51 first-start / restart / configuration checks (Deployment Guide), and in parallel: same username,
email and plant name (also in different letter case), 8 buyers on stock 3, unit price/total during price edits, delete
vs. add/move/sell, login vs. deactivation. Validation order, combined delete messages, partial search and "equal sort
values ordered by ID" also match the SRS.
