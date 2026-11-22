"""M3 - Registration (SRS 7.2) + general API rules (SRS 4.5, 4.6)

Owner: M3. 15 API test cases. No login/logout cases (sir: no test cases for the login function).
Cases marked "Parallel" send the same request several times at the same moment (Postman Collection Runner, or
framework.parallel here). Defect IDs are listed in DEFECT_REPORT.md.
"""
from urllib.parse import quote  # noqa: F401
from client import call, login_client  # noqa: F401
from framework import api_test, verify, parallel  # noqa: F401
from helpers import plant_body, reg_body, post_reg, content, buy, sell  # noqa: F401


@api_test("TC_API_M3_01", 'M3', "Register a new Client with valid data", 'POST /api/client/public/auth/register', 'No token (Guest)',
          '{"fullName":"John Perera","email":"<unique>@example.com","username":"<unique>",'
          '"password":"Passw0rd1","confirmPassword":"Passw0rd1"}',
          "201 Created, success true, data.role = CLIENT, data.status = ACTIVE")
def _(ctx):
    s, b = post_reg(reg_body(ctx))
    return verify(s, b, 201, checks=[("role CLIENT", lambda: b["data"]["role"] == "CLIENT"),
                                     ("status ACTIVE", lambda: b["data"]["status"] == "ACTIVE")])


@api_test("TC_API_M3_02", 'M3', "Registration ignores an extra role=ADMIN field", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'Valid registration body plus "role":"ADMIN"',
          "201 Created, data.role = CLIENT (no Admin account is created)")
def _(ctx):
    s, b = post_reg(reg_body(ctx, role="ADMIN"))
    return verify(s, b, 201, checks=[("role CLIENT", lambda: b["data"]["role"] == "CLIENT")])


@api_test("TC_API_M3_03", 'M3', "Duplicate username with different case is rejected", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'username = existing username in UPPERCASE, new email',
          '409 Conflict, "Username is already taken"', "A Client account already exists.")
def _(ctx):
    first = reg_body(ctx)
    post_reg(first)
    s, b = post_reg(reg_body(ctx, username=first["username"].upper()))
    return verify(s, b, 409, checks=[("'Username is already taken' in response",
                                      lambda: "Username is already taken" in str(b))])


@api_test("TC_API_M3_04", 'M3', "Duplicate email with different case is rejected", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'email = existing email in UPPERCASE, new username',
          '409 Conflict, "Email is already registered"', "A Client account already exists.")
def _(ctx):
    first = reg_body(ctx)
    post_reg(first)
    s, b = post_reg(reg_body(ctx, email=first["email"].upper()))
    return verify(s, b, 409, checks=[("'Email is already registered' in response",
                                      lambda: "Email is already registered" in str(b))])


@api_test("TC_API_M3_05", 'M3', "Admin username is reserved and cannot be registered", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'username = "admin"', '409 Conflict, "Username is already taken"')
def _(ctx):
    s, b = post_reg(reg_body(ctx, username="admin"))
    return verify(s, b, 409, checks=[("'Username is already taken' in response",
                                      lambda: "Username is already taken" in str(b))])


@api_test("TC_API_M3_06", 'M3', "Username with a hyphen is rejected", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'username = "john-01"',
          '400 Bad Request, errors.username = "Username can only contain letters, numbers and underscores"')
def _(ctx):
    s, b = post_reg(reg_body(ctx, username="john-01"))
    return verify(s, b, 400, field="username",
                  field_msg="Username can only contain letters, numbers and underscores")


@api_test("TC_API_M3_07", 'M3', "Email of exactly 100 characters (max boundary) is accepted", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'email = "<33-char name>@<63-char domain>.lk" (exactly 100 characters, valid name@domain.tld format)',
          "201 Created, account registered (SRS 7.2: maximum 100 characters, format name@domain.tld)")
def _(ctx):
    email = ctx.uniq(5).lower() + "a" * 28 + "@" + "d" * 63 + ".lk"
    s, b = post_reg(reg_body(ctx, email=email))
    return verify(s, b, 201, checks=[("email is 100 chars", lambda: len(email) == 100)])


@api_test("TC_API_M3_08", 'M3', "Password without an uppercase letter is rejected", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'password = confirmPassword = "passw0rd1"',
          '400 Bad Request, errors.password = "Password must contain at least one uppercase letter, '
          'one lowercase letter and one number"')
def _(ctx):
    s, b = post_reg(reg_body(ctx, password="passw0rd1", confirmPassword="passw0rd1"))
    return verify(s, b, 400, field="password", field_msg="Password must contain at least one uppercase "
                                                          "letter, one lowercase letter and one number")


@api_test("TC_API_M3_09", 'M3', "Password below minimum length (7 chars)", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'password = confirmPassword = "Abcde12"',
          '400 Bad Request, errors.password = "Password must be between 8 and 20 characters"')
def _(ctx):
    s, b = post_reg(reg_body(ctx, password="Abcde12", confirmPassword="Abcde12"))
    return verify(s, b, 400, field="password", field_msg="Password must be between 8 and 20 characters")


@api_test("TC_API_M3_10", 'M3', "Confirm Password does not match", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'password = "Passw0rd1", confirmPassword = "Passw0rd2"',
          '400 Bad Request, errors.confirmPassword = "Passwords do not match"')
def _(ctx):
    s, b = post_reg(reg_body(ctx, confirmPassword="Passw0rd2"))
    return verify(s, b, 400, field="confirmPassword", field_msg="Passwords do not match")


@api_test("TC_API_M3_11", 'M3', "Email with 1-letter top-level domain is rejected", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'email = "john@mail.c"', '400 Bad Request, errors.email = "Please enter a valid email address"')
def _(ctx):
    s, b = post_reg(reg_body(ctx, email="john@mail.c"))
    return verify(s, b, 400, field="email", field_msg="Please enter a valid email address")


@api_test("TC_API_M3_12", 'M3', "Unsupported HTTP method on the registration endpoint", "GET /api/client/public/auth/register",
          'No token (Guest)', "GET instead of POST",
          '405 Method Not Allowed, message "Method GET is not supported for this endpoint" (SRS 4.6)')
def _(ctx):
    s, b = call("GET", "/api/client/public/auth/register")
    return verify(s, b, 405, "Method GET is not supported for this endpoint")


@api_test("TC_API_M3_13", 'M3', "Registration body that is not JSON", 'POST /api/client/public/auth/register', 'No token (Guest)',
          'Header Content-Type: text/plain; body "username=john_01"',
          '415 Unsupported Media Type, message "Content-Type must be application/json" (SRS 4.6)')
def _(ctx):
    s, b = call("POST", "/api/client/public/auth/register", raw="username=john_01", headers={"Content-Type": "text/plain"})
    return verify(s, b, 415, "Content-Type must be application/json")


@api_test("TC_API_M3_14", 'M3', "Parallel: deleting the same category twice returns 404, not a server error",
          "DELETE /api/admin/categories/{id}", 'Admin token', "5 x DELETE /api/admin/categories/{id} of one empty category, at the same moment",
          '1 x 200 "Category deleted successfully", 4 x 404 "Category not found" (SRS 4.6); no 500',
          precondition="An empty main category exists.",
          steps="1. Send DELETE /api/admin/categories/{id} 5 times at the same moment (Postman Runner, 5 iterations).\n"
                "2. Check every response status and message.")
def _(ctx):
    cat = ctx.main_cat()
    r = parallel(*[lambda: call("DELETE", f"/api/admin/categories/{cat['id']}", token=ctx.admin)] * 5)
    codes = sorted(x[0] for x in r)
    bad = [x for x in r if x[0] not in (200, 404)]
    s, b = bad[0] if bad else r[0]
    return verify(s, b, s, checks=[(f"1 x 200 and 4 x 404, no 500 (got {codes})", lambda: codes == [200, 404, 404, 404, 404])])


@api_test("TC_API_M3_15", 'M3', "Error for a very long search is returned in the standard JSON format",
          "GET /api/client/public/plants?search={9000 chars}", 'No token (Guest)', 'search = "a" repeated 9000 times',
          'A JSON response {"success": ..., "message": ...} (SRS 4.5 "Every API response, successful or not, has the same '
          'structure"), e.g. 200 with an empty list or 400 with a message')
def _(ctx):
    s, b = call("GET", "/api/client/public/plants?search=" + "a" * 9000)
    return verify(s, b, s, checks=[("JSON body with success and message", lambda: isinstance(b, dict) and "success" in b and "message" in b)])
