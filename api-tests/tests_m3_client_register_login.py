"""M3 - Client Registration + Client Login (SRS 5, 5.3, 7.2, 4.3)."""
from client import call
from framework import api_test, verify

M = "M3"
REG = "POST /api/client/public/auth/register"
LOGIN = "POST /api/client/public/auth/login"
NONE = "No token (Guest)"


def reg(ctx, **over):
    u = "r_" + ctx.uniq(8).lower()
    b = {"fullName": "John Perera", "email": f"{u}@example.com", "username": u,
         "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
    b.update(over)
    return b


def post_reg(b):
    return call("POST", "/api/client/public/auth/register", b)


@api_test("TC_API_M3_01", M, "Register a new Client with valid data", REG, NONE,
          '{"fullName":"John Perera","email":"<unique>@example.com","username":"<unique>",'
          '"password":"Passw0rd1","confirmPassword":"Passw0rd1"}',
          "201 Created, success true, data.role = CLIENT, data.status = ACTIVE")
def _(ctx):
    s, b = post_reg(reg(ctx))
    return verify(s, b, 201, checks=[("role CLIENT", lambda: b["data"]["role"] == "CLIENT"),
                                     ("status ACTIVE", lambda: b["data"]["status"] == "ACTIVE")])


@api_test("TC_API_M3_02", M, "Registration ignores an extra role=ADMIN field", REG, NONE,
          'Valid registration body plus "role":"ADMIN"',
          "201 Created, data.role = CLIENT (no Admin account is created)")
def _(ctx):
    s, b = post_reg(reg(ctx, role="ADMIN"))
    return verify(s, b, 201, checks=[("role CLIENT", lambda: b["data"]["role"] == "CLIENT")])


@api_test("TC_API_M3_03", M, "Duplicate username with different case is rejected", REG, NONE,
          'username = existing username in UPPERCASE, new email',
          '409 Conflict, "Username is already taken"', "A Client account already exists.")
def _(ctx):
    first = reg(ctx)
    post_reg(first)
    s, b = post_reg(reg(ctx, username=first["username"].upper()))
    return verify(s, b, 409, checks=[("'Username is already taken' in response",
                                      lambda: "Username is already taken" in str(b))])


@api_test("TC_API_M3_04", M, "Duplicate email with different case is rejected", REG, NONE,
          'email = existing email in UPPERCASE, new username',
          '409 Conflict, "Email is already registered"', "A Client account already exists.")
def _(ctx):
    first = reg(ctx)
    post_reg(first)
    s, b = post_reg(reg(ctx, email=first["email"].upper()))
    return verify(s, b, 409, checks=[("'Email is already registered' in response",
                                      lambda: "Email is already registered" in str(b))])


@api_test("TC_API_M3_05", M, "Admin username is reserved and cannot be registered", REG, NONE,
          'username = "admin"', '409 Conflict, "Username is already taken"')
def _(ctx):
    s, b = post_reg(reg(ctx, username="admin"))
    return verify(s, b, 409, checks=[("'Username is already taken' in response",
                                      lambda: "Username is already taken" in str(b))])


@api_test("TC_API_M3_06", M, "Username with a hyphen is rejected", REG, NONE,
          'username = "john-01"',
          '400 Bad Request, errors.username = "Username can only contain letters, numbers and underscores"')
def _(ctx):
    s, b = post_reg(reg(ctx, username="john-01"))
    return verify(s, b, 400, field="username",
                  field_msg="Username can only contain letters, numbers and underscores")


@api_test("TC_API_M3_07", M, "Email of exactly 100 characters (max boundary) is accepted", REG, NONE,
          'email = "<93-char name>@ex.com" (100 characters, valid name@domain.tld format)',
          "201 Created, account registered (SRS 7.2: maximum 100 characters, format name@domain.tld)")
def _(ctx):
    email = ctx.uniq(5).lower() + "a" * 88 + "@ex.com"
    s, b = post_reg(reg(ctx, email=email))
    return verify(s, b, 201, checks=[("email is 100 chars", lambda: len(email) == 100)])


@api_test("TC_API_M3_08", M, "Password without an uppercase letter is rejected", REG, NONE,
          'password = confirmPassword = "passw0rd1"',
          '400 Bad Request, errors.password = "Password must contain at least one uppercase letter, '
          'one lowercase letter and one number"')
def _(ctx):
    s, b = post_reg(reg(ctx, password="passw0rd1", confirmPassword="passw0rd1"))
    return verify(s, b, 400, field="password", field_msg="Password must contain at least one uppercase "
                                                          "letter, one lowercase letter and one number")


@api_test("TC_API_M3_09", M, "Password below minimum length (7 chars)", REG, NONE,
          'password = confirmPassword = "Abcde12"',
          '400 Bad Request, errors.password = "Password must be between 8 and 20 characters"')
def _(ctx):
    s, b = post_reg(reg(ctx, password="Abcde12", confirmPassword="Abcde12"))
    return verify(s, b, 400, field="password", field_msg="Password must be between 8 and 20 characters")


@api_test("TC_API_M3_10", M, "Confirm Password does not match", REG, NONE,
          'password = "Passw0rd1", confirmPassword = "Passw0rd2"',
          '400 Bad Request, errors.confirmPassword = "Passwords do not match"')
def _(ctx):
    s, b = post_reg(reg(ctx, confirmPassword="Passw0rd2"))
    return verify(s, b, 400, field="confirmPassword", field_msg="Passwords do not match")


@api_test("TC_API_M3_11", M, "Email with 1-letter top-level domain is rejected", REG, NONE,
          'email = "john@mail.c"', '400 Bad Request, errors.email = "Please enter a valid email address"')
def _(ctx):
    s, b = post_reg(reg(ctx, email="john@mail.c"))
    return verify(s, b, 400, field="email", field_msg="Please enter a valid email address")


@api_test("TC_API_M3_12", M, "Client login with valid credentials", LOGIN, NONE,
          '{"username":"user","password":"User@123"}',
          '200 OK, message "Login successful", data.token returned')
def _(ctx):
    s, b = call("POST", "/api/client/public/auth/login", {"username": "user", "password": "User@123"})
    return verify(s, b, 200, "Login successful", checks=[("token present", lambda: b["data"]["token"])])


@api_test("TC_API_M3_13", M, "Admin credentials rejected on Client login", LOGIN, NONE,
          '{"username":"admin","password":"Admin@123"}',
          '403 Forbidden, message "Please use the Admin App to sign in."')
def _(ctx):
    s, b = call("POST", "/api/client/public/auth/login", {"username": "admin", "password": "Admin@123"})
    return verify(s, b, 403, "Please use the Admin App to sign in.")


@api_test("TC_API_M3_14", M, "Inactive Client with correct password cannot log in", LOGIN, NONE,
          "Username/password of a Client deactivated by Admin",
          '403 Forbidden, message "Your account is inactive. Please contact support."',
          "A Client account exists and has been deactivated by the Admin.")
def _(ctx):
    c = ctx.new_client(login=False)
    call("PATCH", f"/api/admin/users/{c['id']}/deactivate", token=ctx.admin)
    s, b = call("POST", "/api/client/public/auth/login", {"username": c["username"], "password": c["password"]})
    return verify(s, b, 403, "Your account is inactive. Please contact support.")


@api_test("TC_API_M3_15", M, "Inactive Client with wrong password gets generic error", LOGIN, NONE,
          "Username of a deactivated Client, password = Wrong@999",
          '401 Unauthorized, message "Invalid username or password." (status not revealed)',
          "A Client account exists and has been deactivated by the Admin.")
def _(ctx):
    c = ctx.new_client(login=False)
    call("PATCH", f"/api/admin/users/{c['id']}/deactivate", token=ctx.admin)
    s, b = call("POST", "/api/client/public/auth/login", {"username": c["username"], "password": "Wrong@999"})
    return verify(s, b, 401, "Invalid username or password.")
