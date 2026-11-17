"""M1 - Admin Authentication + Category Management (SRS 5, 6.1, 6.3, 4.2)."""
from client import call, login_admin
from framework import api_test, verify

M = "M1"
LOGIN = "POST /api/admin/auth/login"
CAT = "POST /api/admin/categories"
ADMIN = "Admin token"
NONE = "No token"


@api_test("TC_API_M1_01", M, "Admin login with valid credentials", LOGIN, NONE,
          '{"username":"admin","password":"Admin@123"}',
          '200 OK, message "Login successful", data.token is returned')
def _(ctx):
    s, b = call("POST", "/api/admin/auth/login", {"username": "admin", "password": "Admin@123"})
    return verify(s, b, 200, "Login successful", checks=[("token present", lambda: b["data"]["token"])])


@api_test("TC_API_M1_02", M, "Admin login with wrong password", LOGIN, NONE,
          '{"username":"admin","password":"Wrong@123"}',
          '401 Unauthorized, message "Invalid username or password."')
def _(ctx):
    s, b = call("POST", "/api/admin/auth/login", {"username": "admin", "password": "Wrong@123"})
    return verify(s, b, 401, "Invalid username or password.")


@api_test("TC_API_M1_03", M, "Admin login with empty username", LOGIN, NONE,
          '{"username":"","password":"Admin@123"}',
          '400 Bad Request, errors.username = "Username is required"')
def _(ctx):
    s, b = call("POST", "/api/admin/auth/login", {"username": "", "password": "Admin@123"})
    return verify(s, b, 400, field="username", field_msg="Username is required")


@api_test("TC_API_M1_04", M, "Admin username is trimmed and not case-sensitive", LOGIN, NONE,
          '{"username":"  ADMIN  ","password":"Admin@123"}',
          '200 OK, message "Login successful", token returned')
def _(ctx):
    s, b = call("POST", "/api/admin/auth/login", {"username": "  ADMIN  ", "password": "Admin@123"})
    return verify(s, b, 200, "Login successful")


@api_test("TC_API_M1_05", M, "Admin password is case-sensitive", LOGIN, NONE,
          '{"username":"admin","password":"admin@123"}',
          '401 Unauthorized, message "Invalid username or password."')
def _(ctx):
    s, b = call("POST", "/api/admin/auth/login", {"username": "admin", "password": "admin@123"})
    return verify(s, b, 401, "Invalid username or password.")


@api_test("TC_API_M1_06", M, "Client credentials rejected on Admin login", LOGIN, NONE,
          '{"username":"user","password":"User@123"}',
          '403 Forbidden, message "You are not authorized to access the Admin App."')
def _(ctx):
    s, b = call("POST", "/api/admin/auth/login", {"username": "user", "password": "User@123"})
    return verify(s, b, 403, "You are not authorized to access the Admin App.")


@api_test("TC_API_M1_07", M, "Admin token is invalid after logout",
          "POST /api/admin/auth/logout", ADMIN, "Fresh admin token; then GET /api/admin/categories with same token",
          'Logout 200; next call with the same token 401, message "Invalid or expired token"',
          steps="1. Log in as admin and copy the token.\n2. Send POST /api/admin/auth/logout with the token.\n"
                "3. Send GET /api/admin/categories with the same token.\n4. Check status and message.")
def _(ctx):
    t = login_admin()
    s1, _b = call("POST", "/api/admin/auth/logout", token=t)
    s, b = call("GET", "/api/admin/categories", token=t)
    return verify(s, b, 401, "Invalid or expired token", checks=[("logout returned 200", lambda: s1 == 200)])


@api_test("TC_API_M1_08", M, "Create a main category", CAT, ADMIN,
          '{"name":"<unique 7 chars>","parentId":null}',
          '201 Created, message "Category created successfully", data.parentId is null')
def _(ctx):
    name = "M" + ctx.uniq(6)
    s, b = call("POST", "/api/admin/categories", {"name": name, "parentId": None}, ctx.admin)
    return verify(s, b, 201, "Category created successfully",
                  checks=[("name saved", lambda: b["data"]["name"] == name),
                          ("parentId null", lambda: b["data"].get("parentId") is None)])


@api_test("TC_API_M1_09", M, "Create a sub-category under a main category", CAT, ADMIN,
          '{"name":"<unique>","parentId":<main category id>}',
          '201 Created, message "Category created successfully", data.parentId = main category id',
          precondition="A main category exists.")
def _(ctx):
    main = ctx.main_cat()
    s, b = call("POST", "/api/admin/categories", {"name": "S" + ctx.uniq(6), "parentId": main["id"]}, ctx.admin)
    return verify(s, b, 201, "Category created successfully",
                  checks=[("parentId set", lambda: b["data"]["parentId"] == main["id"])])


@api_test("TC_API_M1_10", M, "Category name is required", CAT, ADMIN,
          '{"name":"","parentId":null}',
          '400 Bad Request, errors.name = "Category name is required"')
def _(ctx):
    s, b = call("POST", "/api/admin/categories", {"name": "", "parentId": None}, ctx.admin)
    return verify(s, b, 400, field="name", field_msg="Category name is required")


@api_test("TC_API_M1_11", M, "Category name below minimum length (2 chars)", CAT, ADMIN,
          '{"name":"AB","parentId":null}',
          '400 Bad Request, errors.name = "Category name must be between 3 and 10 characters"')
def _(ctx):
    s, b = call("POST", "/api/admin/categories", {"name": "AB", "parentId": None}, ctx.admin)
    return verify(s, b, 400, field="name", field_msg="Category name must be between 3 and 10 characters")


@api_test("TC_API_M1_12", M, "Duplicate category name (different case) under same parent", CAT, ADMIN,
          'Existing main category "<name>"; send {"name":"<name in lowercase>","parentId":null}',
          '409 Conflict, message/errors.name "Category name already exists"',
          precondition="A main category exists.")
def _(ctx):
    main = ctx.main_cat()
    s, b = call("POST", "/api/admin/categories", {"name": main["name"].lower(), "parentId": None}, ctx.admin)
    text = str(b)
    return verify(s, b, 409, checks=[("'Category name already exists' in response",
                                      lambda: "Category name already exists" in text)])


@api_test("TC_API_M1_13", M, "Sub-category cannot be used as a parent", CAT, ADMIN,
          '{"name":"<unique>","parentId":<sub-category id>}',
          '400 Bad Request, errors.parentId = "Parent category must be a main category"',
          precondition="A sub-category exists.")
def _(ctx):
    sub = ctx.sub_cat()
    s, b = call("POST", "/api/admin/categories", {"name": "X" + ctx.uniq(6), "parentId": sub["id"]}, ctx.admin)
    return verify(s, b, 400, field="parentId", field_msg="Parent category must be a main category")


@api_test("TC_API_M1_14", M, "Delete main category that has 1 sub-category",
          "DELETE /api/admin/categories/{id}", ADMIN, "id = main category with exactly 1 sub-category",
          '409 Conflict, message "Category cannot be deleted because it has 1 sub-category."',
          precondition="A main category with exactly one sub-category exists.")
def _(ctx):
    main = ctx.main_cat()
    ctx.sub_cat(main["id"])
    s, b = call("DELETE", f"/api/admin/categories/{main['id']}", token=ctx.admin)
    return verify(s, b, 409, "Category cannot be deleted because it has 1 sub-category.")


@api_test("TC_API_M1_15", M, "Client token cannot create a category", CAT, "Client token (user)",
          '{"name":"Indoor","parentId":null}',
          '403 Forbidden, message "You do not have permission to access this resource"')
def _(ctx):
    s, b = call("POST", "/api/admin/categories", {"name": "Indoor", "parentId": None}, ctx.client)
    return verify(s, b, 403, "You do not have permission to access this resource")
