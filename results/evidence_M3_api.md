# M3 API test execution evidence

- Executed: 2026-11-20 15:53:59 UTC
- Base URL: http://localhost:8080  (QA Training App jar, MySQL 8.0 database)
- Tokens are replaced with `<JWT token>`; test passwords are test data from the test case.

**Result: 15 Passed, 0 Failed, 0 Blocked**

## TC_API_M3_01 - Register a new Client with valid data - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 201 Created, success true, data.role = CLIENT, data.status = ACTIVE
- Actual: 201, message='Registration successful. Please log in.'

1. `POST /api/client/public/auth/register` (auth: none) -> **201**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_fibzowqe@example.com", "username": "r_fibzowqe", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": true, "message": "Registration successful. Please log in.", "data": {"id": 12, "username": "r_fibzowqe", "fullName": "John Perera", "email": "r_fibzowqe@example.com", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:53:59.510399Z"}}
   ```

## TC_API_M3_02 - Registration ignores an extra role=ADMIN field - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 201 Created, data.role = CLIENT (no Admin account is created)
- Actual: 201, message='Registration successful. Please log in.'

1. `POST /api/client/public/auth/register` (auth: none) -> **201**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_xvjkupce@example.com", "username": "r_xvjkupce", "password": "Passw0rd1", "confirmPassword": "Passw0rd1", "role": "ADMIN"}
   ```
   Response:
   ```json
   {"success": true, "message": "Registration successful. Please log in.", "data": {"id": 13, "username": "r_xvjkupce", "fullName": "John Perera", "email": "r_xvjkupce@example.com", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:53:59.609498Z"}}
   ```

## TC_API_M3_03 - Duplicate username with different case is rejected - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 409 Conflict, "Username is already taken"
- Actual: 409, message='Validation failed', errors={"username": "Username is already taken"}

1. `POST /api/client/public/auth/register` (auth: none) -> **201**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_yhhxkjpi@example.com", "username": "r_yhhxkjpi", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": true, "message": "Registration successful. Please log in.", "data": {"id": 14, "username": "r_yhhxkjpi", "fullName": "John Perera", "email": "r_yhhxkjpi@example.com", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:53:59.708269Z"}}
   ```

2. `POST /api/client/public/auth/register` (auth: none) -> **409**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_gthpvbvp@example.com", "username": "R_YHHXKJPI", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"username": "Username is already taken"}}
   ```

## TC_API_M3_04 - Duplicate email with different case is rejected - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 409 Conflict, "Email is already registered"
- Actual: 409, message='Validation failed', errors={"email": "Email is already registered"}

1. `POST /api/client/public/auth/register` (auth: none) -> **201**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_szfvhgja@example.com", "username": "r_szfvhgja", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": true, "message": "Registration successful. Please log in.", "data": {"id": 15, "username": "r_szfvhgja", "fullName": "John Perera", "email": "r_szfvhgja@example.com", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:53:59.811140Z"}}
   ```

2. `POST /api/client/public/auth/register` (auth: none) -> **409**

   Request:
   ```json
   {"fullName": "John Perera", "email": "R_SZFVHGJA@EXAMPLE.COM", "username": "r_gnxqjmfy", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"email": "Email is already registered"}}
   ```

## TC_API_M3_05 - Admin username is reserved and cannot be registered - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 409 Conflict, "Username is already taken"
- Actual: 409, message='Validation failed', errors={"username": "Username is already taken"}

1. `POST /api/client/public/auth/register` (auth: none) -> **409**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_blqfvlky@example.com", "username": "admin", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"username": "Username is already taken"}}
   ```

## TC_API_M3_06 - Username with a hyphen is rejected - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 400 Bad Request, errors.username = "Username can only contain letters, numbers and underscores"
- Actual: 400, message='Validation failed', errors={"username": "Username can only contain letters, numbers and underscores"}

1. `POST /api/client/public/auth/register` (auth: none) -> **400**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_uqqwrvhr@example.com", "username": "john-01", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"username": "Username can only contain letters, numbers and underscores"}}
   ```

## TC_API_M3_07 - Email of exactly 100 characters (max boundary) is accepted - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 201 Created, account registered (SRS 7.2: maximum 100 characters, format name@domain.tld)
- Actual: 201, message='Registration successful. Please log in.'

1. `POST /api/client/public/auth/register` (auth: none) -> **201**

   Request:
   ```json
   {"fullName": "John Perera", "email": "lzpqqaaaaaaaaaaaaaaaaaaaaaaaaaaaa@ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd.lk", "username": "r_aaiyasgu", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": true, "message": "Registration successful. Please log in.", "data": {"id": 16, "username": "r_aaiyasgu", "fullName": "John Perera", "email": "lzpqqaaaaaaaaaaaaaaaaaaaaaaaaaaaa@ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd.lk", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:53:59.940030Z"}}
   ```

## TC_API_M3_08 - Password without an uppercase letter is rejected - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 400 Bad Request, errors.password = "Password must contain at least one uppercase letter, one lowercase letter and one number"
- Actual: 400, message='Validation failed', errors={"password": "Password must contain at least one uppercase letter, one lowercase letter and one number"}

1. `POST /api/client/public/auth/register` (auth: none) -> **400**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_mkqoblax@example.com", "username": "r_mkqoblax", "password": "passw0rd1", "confirmPassword": "passw0rd1"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"password": "Password must contain at least one uppercase letter, one lowercase letter and one number"}}
   ```

## TC_API_M3_09 - Password below minimum length (7 chars) - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 400 Bad Request, errors.password = "Password must be between 8 and 20 characters"
- Actual: 400, message='Validation failed', errors={"password": "Password must be between 8 and 20 characters"}

1. `POST /api/client/public/auth/register` (auth: none) -> **400**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_sforslit@example.com", "username": "r_sforslit", "password": "Abcde12", "confirmPassword": "Abcde12"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"password": "Password must be between 8 and 20 characters"}}
   ```

## TC_API_M3_10 - Confirm Password does not match - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 400 Bad Request, errors.confirmPassword = "Passwords do not match"
- Actual: 400, message='Validation failed', errors={"confirmPassword": "Passwords do not match"}

1. `POST /api/client/public/auth/register` (auth: none) -> **400**

   Request:
   ```json
   {"fullName": "John Perera", "email": "r_lozhfeei@example.com", "username": "r_lozhfeei", "password": "Passw0rd1", "confirmPassword": "Passw0rd2"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"confirmPassword": "Passwords do not match"}}
   ```

## TC_API_M3_11 - Email with 1-letter top-level domain is rejected - **Passed**

- Endpoint: `POST /api/client/public/auth/register`  |  Role: No token (Guest)
- Expected: 400 Bad Request, errors.email = "Please enter a valid email address"
- Actual: 400, message='Validation failed', errors={"email": "Please enter a valid email address"}

1. `POST /api/client/public/auth/register` (auth: none) -> **400**

   Request:
   ```json
   {"fullName": "John Perera", "email": "john@mail.c", "username": "r_bfidhqif", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": false, "message": "Validation failed", "errors": {"email": "Please enter a valid email address"}}
   ```

## TC_API_M3_12 - Client login with valid credentials - **Passed**

- Endpoint: `POST /api/client/public/auth/login`  |  Role: No token (Guest)
- Expected: 200 OK, message "Login successful", data.token returned
- Actual: 200, message='Login successful'

1. `POST /api/client/public/auth/login` (auth: none) -> **200**

   Request:
   ```json
   {"username": "user", "password": "User@123"}
   ```
   Response:
   ```json
   {"success": true, "message": "Login successful", "data": {"token": "<JWT token>", "tokenType": "Bearer", "expiresAt": "2026-11-20T23:54:00.129816Z", "user": {"id": 2, "username": "user", "fullName": "Test Client", "email": "user@qatraining.local", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:51:53.105323Z"}}}
   ```

## TC_API_M3_13 - Admin credentials rejected on Client login - **Passed**

- Endpoint: `POST /api/client/public/auth/login`  |  Role: No token (Guest)
- Expected: 403 Forbidden, message "Please use the Admin App to sign in."
- Actual: 403, message='Please use the Admin App to sign in.'

1. `POST /api/client/public/auth/login` (auth: none) -> **403**

   Request:
   ```json
   {"username": "admin", "password": "Admin@123"}
   ```
   Response:
   ```json
   {"success": false, "message": "Please use the Admin App to sign in."}
   ```

## TC_API_M3_14 - Inactive Client with correct password cannot log in - **Passed**

- Endpoint: `POST /api/client/public/auth/login`  |  Role: No token (Guest)
- Expected: 403 Forbidden, message "Your account is inactive. Please contact support."
- Actual: 403, message='Your account is inactive. Please contact support.'

1. `POST /api/client/public/auth/register` (auth: none) -> **201**

   Request:
   ```json
   {"fullName": "Test u_bbyiudov", "email": "u_bbyiudov@mail.com", "username": "u_bbyiudov", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": true, "message": "Registration successful. Please log in.", "data": {"id": 17, "username": "u_bbyiudov", "fullName": "Test u_bbyiudov", "email": "u_bbyiudov@mail.com", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:54:00.315326Z"}}
   ```

2. `PATCH /api/admin/users/17/deactivate` (auth: Bearer <token>) -> **200**

   Response:
   ```json
   {"success": true, "message": "User deactivated successfully.", "data": {"id": 17, "username": "u_bbyiudov", "fullName": "Test u_bbyiudov", "email": "u_bbyiudov@mail.com", "role": "CLIENT", "status": "INACTIVE", "registeredAt": "2026-11-20T15:54:00.315326Z"}}
   ```

3. `POST /api/client/public/auth/login` (auth: none) -> **403**

   Request:
   ```json
   {"username": "u_bbyiudov", "password": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": false, "message": "Your account is inactive. Please contact support."}
   ```

## TC_API_M3_15 - Inactive Client with wrong password gets generic error - **Passed**

- Endpoint: `POST /api/client/public/auth/login`  |  Role: No token (Guest)
- Expected: 401 Unauthorized, message "Invalid username or password." (status not revealed)
- Actual: 401, message='Invalid username or password.'

1. `POST /api/client/public/auth/register` (auth: none) -> **201**

   Request:
   ```json
   {"fullName": "Test u_lmhigeee", "email": "u_lmhigeee@mail.com", "username": "u_lmhigeee", "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
   ```
   Response:
   ```json
   {"success": true, "message": "Registration successful. Please log in.", "data": {"id": 18, "username": "u_lmhigeee", "fullName": "Test u_lmhigeee", "email": "u_lmhigeee@mail.com", "role": "CLIENT", "status": "ACTIVE", "registeredAt": "2026-11-20T15:54:00.527403Z"}}
   ```

2. `PATCH /api/admin/users/18/deactivate` (auth: Bearer <token>) -> **200**

   Response:
   ```json
   {"success": true, "message": "User deactivated successfully.", "data": {"id": 18, "username": "u_lmhigeee", "fullName": "Test u_lmhigeee", "email": "u_lmhigeee@mail.com", "role": "CLIENT", "status": "INACTIVE", "registeredAt": "2026-11-20T15:54:00.527403Z"}}
   ```

3. `POST /api/client/public/auth/login` (auth: none) -> **401**

   Request:
   ```json
   {"username": "u_lmhigeee", "password": "Wrong@999"}
   ```
   Response:
   ```json
   {"success": false, "message": "Invalid username or password."}
   ```

