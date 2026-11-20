# M1 API test execution evidence

- Executed: 2026-11-20 17:08:01 UTC
- Base URL: http://localhost:8080  (QA Training App jar, MySQL 8.0 database)
- Tokens are replaced with `<JWT token>`; passwords are the test data from the test case.

**Result: 15 Passed, 0 Failed, 0 Blocked**

## TC_API_M1_01 - Admin login with valid credentials - **Passed**

- Endpoint: `POST /api/admin/auth/login`  |  Role: No token
- Expected: 200 OK, message "Login successful", data.token is returned
- Actual: 200, message='Login successful'

1. `POST /api/admin/auth/login` (auth: none) -> **200**

   Request:
   ```json
   {"username": "admin", "password": "Admin@123"}
   ```
   Response:
   ```json
   {"success": true, "message": "Login successful", "data": {"token": "<JWT token>", "tokenType": "Bearer", "expiresAt": "2026-11-21T01:08:00.504333500Z", "user": {"id": 1, "username": "admin", "fullName": "Store Administrator", "email": "admin@qatraining.local", "role": "ADMIN", "status": "ACTIVE", "registeredAt": "2026-11-18T11:01:34.568775Z"}}}
   ```

## TC_API_M1_02 - Admin login with wrong password - **Passed**

- Endpoint: `POST /api/admin/auth/login`  |  Role: No token
- Expected: 401 Unauthorized, message "Invalid username or password."
- Actual: 401, message='Invalid username or password.'

1. `POST /api/admin/auth/login` (auth: none) -> **401**

   Request:
   ```json
   {"username": "admin", "password": "Wrong@123"}
   ```
   Response:
   ```json
   {"success": false, "message": "Invalid username or password."}
   ```

## TC_API_M1_03 - Admin login with empty username - **Passed**

- Endpoint: `POST /api/admin/auth/login`  |  Role: No token
- Expected: 400 Bad Request, errors.username = "Username is required"
- Actual: 400, message='Validation failed', errors={"username": "Username is required"}

1. `POST /api/admin/auth/login` (auth: none) -> **400**

   Request:
   ```json
   {"username": "", "password": "Admin@123"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"username": "Username is required"}}
   ```

## TC_API_M1_04 - Admin username is trimmed and not case-sensitive - **Passed**

- Endpoint: `POST /api/admin/auth/login`  |  Role: No token
- Expected: 200 OK, message "Login successful", token returned
- Actual: 200, message='Login successful'

1. `POST /api/admin/auth/login` (auth: none) -> **200**

   Request:
   ```json
   {"username": "  ADMIN  ", "password": "Admin@123"}
   ```
   Response:
   ```json
   {"success": true, "message": "Login successful", "data": {"token": "<JWT token>", "tokenType": "Bearer", "expiresAt": "2026-11-21T01:08:00.724334700Z", "user": {"id": 1, "username": "admin", "fullName": "Store Administrator", "email": "admin@qatraining.local", "role": "ADMIN", "status": "ACTIVE", "registeredAt": "2026-11-18T11:01:34.568775Z"}}}
   ```

## TC_API_M1_05 - Admin password is case-sensitive - **Passed**

- Endpoint: `POST /api/admin/auth/login`  |  Role: No token
- Expected: 401 Unauthorized, message "Invalid username or password."
- Actual: 401, message='Invalid username or password.'

1. `POST /api/admin/auth/login` (auth: none) -> **401**

   Request:
   ```json
   {"username": "admin", "password": "admin@123"}
   ```
   Response:
   ```json
   {"success": false, "message": "Invalid username or password."}
   ```

## TC_API_M1_06 - Client credentials rejected on Admin login - **Passed**

- Endpoint: `POST /api/admin/auth/login`  |  Role: No token
- Expected: 403 Forbidden, message "You are not authorized to access the Admin App."
- Actual: 403, message='You are not authorized to access the Admin App.'

1. `POST /api/admin/auth/login` (auth: none) -> **403**

   Request:
   ```json
   {"username": "user", "password": "User@123"}
   ```
   Response:
   ```json
   {"success": false, "message": "You are not authorized to access the Admin App."}
   ```

## TC_API_M1_07 - Admin token is invalid after logout - **Passed**

- Endpoint: `POST /api/admin/auth/logout`  |  Role: Admin token
- Expected: Logout 200; next call with the same token 401, message "Invalid or expired token"
- Actual: 401, message='Invalid or expired token'

1. `POST /api/admin/auth/login` (auth: none) -> **200**

   Request:
   ```json
   {"username": "admin", "password": "Admin@123"}
   ```
   Response:
   ```json
   {"success": true, "message": "Login successful", "data": {"token": "<JWT token>", "tokenType": "Bearer", "expiresAt": "2026-11-21T01:08:01.063312200Z", "user": {"id": 1, "username": "admin", "fullName": "Store Administrator", "email": "admin@qatraining.local", "role": "ADMIN", "status": "ACTIVE", "registeredAt": "2026-11-18T11:01:34.568775Z"}}}
   ```

2. `POST /api/admin/auth/logout` (auth: Bearer <JWT token>) -> **200**

   Response:
   ```json
   {"success": true, "message": "You have been logged out successfully."}
   ```

3. `GET /api/admin/categories` (auth: Bearer <JWT token>) -> **401**

   Response:
   ```json
   {"success": false, "message": "Invalid or expired token"}
   ```

## TC_API_M1_08 - Create a main category - **Passed**

- Endpoint: `POST /api/admin/categories`  |  Role: Admin token
- Expected: 201 Created, message "Category created successfully", data.parentId is null
- Actual: 201, message='Category created successfully'

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "MOSNTBU", "parentId": null}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 242, "name": "MOSNTBU", "parentId": null, "parentName": null}}
   ```

## TC_API_M1_09 - Create a sub-category under a main category - **Passed**

- Endpoint: `POST /api/admin/categories`  |  Role: Admin token
- Expected: 201 Created, message "Category created successfully", data.parentId = main category id
- Actual: 201, message='Category created successfully'

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "MZTGCFS", "parentId": null}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 243, "name": "MZTGCFS", "parentId": null, "parentName": null}}
   ```

2. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "SHKJFAF", "parentId": 243}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 244, "name": "SHKJFAF", "parentId": 243, "parentName": "MZTGCFS"}}
   ```

## TC_API_M1_10 - Category name is required - **Passed**

- Endpoint: `POST /api/admin/categories`  |  Role: Admin token
- Expected: 400 Bad Request, errors.name = "Category name is required"
- Actual: 400, message='Validation failed', errors={"name": "Category name is required"}

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **400**

   Request:
   ```json
   {"name": "", "parentId": null}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"name": "Category name is required"}}
   ```

## TC_API_M1_11 - Category name below minimum length (2 chars) - **Passed**

- Endpoint: `POST /api/admin/categories`  |  Role: Admin token
- Expected: 400 Bad Request, errors.name = "Category name must be between 3 and 10 characters"
- Actual: 400, message='Validation failed', errors={"name": "Category name must be between 3 and 10 characters"}

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **400**

   Request:
   ```json
   {"name": "AB", "parentId": null}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"name": "Category name must be between 3 and 10 characters"}}
   ```

## TC_API_M1_12 - Duplicate category name (different case) under same parent - **Passed**

- Endpoint: `POST /api/admin/categories`  |  Role: Admin token
- Expected: 409 Conflict, errors.name = "Category name already exists"
- Actual: 409, message='Validation failed', errors={"name": "Category name already exists"}

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "MTXOAIQ", "parentId": null}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 245, "name": "MTXOAIQ", "parentId": null, "parentName": null}}
   ```

2. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **409**

   Request:
   ```json
   {"name": "mtxoaiq", "parentId": null}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"name": "Category name already exists"}}
   ```

## TC_API_M1_13 - Sub-category cannot be used as a parent - **Passed**

- Endpoint: `POST /api/admin/categories`  |  Role: Admin token
- Expected: 400 Bad Request, errors.parentId = "Parent category must be a main category"
- Actual: 400, message='Validation failed', errors={"parentId": "Parent category must be a main category"}

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "MBNTMHJ", "parentId": null}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 246, "name": "MBNTMHJ", "parentId": null, "parentName": null}}
   ```

2. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "SXRYHTN", "parentId": 246}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 247, "name": "SXRYHTN", "parentId": 246, "parentName": "MBNTMHJ"}}
   ```

3. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **400**

   Request:
   ```json
   {"name": "XOCYETK", "parentId": 247}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"parentId": "Parent category must be a main category"}}
   ```

## TC_API_M1_14 - Delete main category that has 1 sub-category - **Passed**

- Endpoint: `DELETE /api/admin/categories/{id}`  |  Role: Admin token
- Expected: 409 Conflict, message "Category cannot be deleted because it has 1 sub-category."
- Actual: 409, message='Category cannot be deleted because it has 1 sub-category.'

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "MRTGQAA", "parentId": null}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 248, "name": "MRTGQAA", "parentId": null, "parentName": null}}
   ```

2. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **201**

   Request:
   ```json
   {"name": "SBIVNDG", "parentId": 248}
   ```
   Response:
   ```json
   {"success": true, "message": "Category created successfully", "data": {"id": 249, "name": "SBIVNDG", "parentId": 248, "parentName": "MRTGQAA"}}
   ```

3. `DELETE /api/admin/categories/248` (auth: Bearer <JWT token>) -> **409**

   Response:
   ```json
   {"success": false, "message": "Category cannot be deleted because it has 1 sub-category."}
   ```

## TC_API_M1_15 - Client token cannot create a category - **Passed**

- Endpoint: `POST /api/admin/categories`  |  Role: Client token (user)
- Expected: 403 Forbidden, message "You do not have permission to access this resource"
- Actual: 403, message='You do not have permission to access this resource'

1. `POST /api/admin/categories` (auth: Bearer <JWT token>) -> **403**

   Request:
   ```json
   {"name": "Indoor", "parentId": null}
   ```
   Response:
   ```json
   {"success": false, "message": "You do not have permission to access this resource"}
   ```
