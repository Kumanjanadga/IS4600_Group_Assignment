"""M1 - Category Management (SRS 6.3) + Dashboard (SRS 6.2)

Owner: M1. 15 API test cases. No login/logout cases (sir: no test cases for the login function).
Cases marked "Parallel" send the same request several times at the same moment (Postman Collection Runner, or
framework.parallel here). Defect IDs are listed in DEFECT_REPORT.md.
"""
from urllib.parse import quote  # noqa: F401
from client import call, login_client  # noqa: F401
from framework import api_test, verify, parallel  # noqa: F401
from helpers import plant_body, reg_body, post_reg, content, buy, sell  # noqa: F401


@api_test("TC_API_M1_01", 'M1', "Create a main category", 'POST /api/admin/categories', 'Admin token',
          '{"name":"<unique 7 chars>","parentId":null}',
          '201 Created, message "Category created successfully", data.parentId is null')
def _(ctx):
    name = "M" + ctx.uniq(6)
    s, b = call("POST", "/api/admin/categories", {"name": name, "parentId": None}, ctx.admin)
    return verify(s, b, 201, "Category created successfully",
                  checks=[("name saved", lambda: b["data"]["name"] == name),
                          ("parentId null", lambda: b["data"].get("parentId") is None)])


@api_test("TC_API_M1_02", 'M1', "Create a sub-category under a main category", 'POST /api/admin/categories', 'Admin token',
          '{"name":"<unique>","parentId":<main category id>}',
          '201 Created, message "Category created successfully", data.parentId = main category id',
          precondition="A main category exists.")
def _(ctx):
    main = ctx.main_cat()
    s, b = call("POST", "/api/admin/categories", {"name": "S" + ctx.uniq(6), "parentId": main["id"]}, ctx.admin)
    return verify(s, b, 201, "Category created successfully",
                  checks=[("parentId set", lambda: b["data"]["parentId"] == main["id"])])


@api_test("TC_API_M1_03", 'M1', "Category name is required", 'POST /api/admin/categories', 'Admin token',
          '{"name":"","parentId":null}',
          '400 Bad Request, errors.name = "Category name is required"')
def _(ctx):
    s, b = call("POST", "/api/admin/categories", {"name": "", "parentId": None}, ctx.admin)
    return verify(s, b, 400, field="name", field_msg="Category name is required")


@api_test("TC_API_M1_04", 'M1', "Category name below minimum length (2 chars)", 'POST /api/admin/categories', 'Admin token',
          '{"name":"AB","parentId":null}',
          '400 Bad Request, errors.name = "Category name must be between 3 and 10 characters"')
def _(ctx):
    s, b = call("POST", "/api/admin/categories", {"name": "AB", "parentId": None}, ctx.admin)
    return verify(s, b, 400, field="name", field_msg="Category name must be between 3 and 10 characters")


@api_test("TC_API_M1_05", 'M1', "Duplicate category name (different case) under same parent", 'POST /api/admin/categories', 'Admin token',
          'Existing main category "<name>"; send {"name":"<name in lowercase>","parentId":null}',
          '409 Conflict, errors.name = "Category name already exists"',
          precondition="A main category exists.")
def _(ctx):
    main = ctx.main_cat()
    s, b = call("POST", "/api/admin/categories", {"name": main["name"].lower(), "parentId": None}, ctx.admin)
    return verify(s, b, 409, field="name", field_msg="Category name already exists")


@api_test("TC_API_M1_06", 'M1', "Sub-category cannot be used as a parent", 'POST /api/admin/categories', 'Admin token',
          '{"name":"<unique>","parentId":<sub-category id>}',
          '400 Bad Request, errors.parentId = "Parent category must be a main category"',
          precondition="A sub-category exists.")
def _(ctx):
    sub = ctx.sub_cat()
    s, b = call("POST", "/api/admin/categories", {"name": "X" + ctx.uniq(6), "parentId": sub["id"]}, ctx.admin)
    return verify(s, b, 400, field="parentId", field_msg="Parent category must be a main category")


@api_test("TC_API_M1_07", 'M1', "Delete main category that has 1 sub-category",
          "DELETE /api/admin/categories/{id}", 'Admin token', "id = main category with exactly 1 sub-category",
          '409 Conflict, message "Category cannot be deleted because it has 1 sub-category."',
          precondition="A main category with exactly one sub-category exists.")
def _(ctx):
    main = ctx.main_cat()
    ctx.sub_cat(main["id"])
    s, b = call("DELETE", f"/api/admin/categories/{main['id']}", token=ctx.admin)
    return verify(s, b, 409, "Category cannot be deleted because it has 1 sub-category.")


@api_test("TC_API_M1_08", 'M1', "Client token cannot create a category", 'POST /api/admin/categories', "Client token (user)",
          '{"name":"Indoor","parentId":null}',
          '403 Forbidden, message "You do not have permission to access this resource"')
def _(ctx):
    s, b = call("POST", "/api/admin/categories", {"name": "Indoor", "parentId": None}, ctx.client)
    return verify(s, b, 403, "You do not have permission to access this resource")


@api_test("TC_API_M1_09", 'M1', "Dashboard low-stock count includes quantity 0 and 4, not 5",
          "GET /api/admin/dashboard/summary", 'Admin token',
          "Read summary; add plants with quantity 0, 4 and 5; read summary again",
          "200 OK, plants.total +3 and plants.lowStock +2",
          steps="1. Send GET /api/admin/dashboard/summary and note plants.total and plants.lowStock.\n"
                "2. Add three plants with quantity 0, 4 and 5.\n3. Send GET /api/admin/dashboard/summary again.\n"
                "4. Compare the counts.")
def _(ctx):
    _s, before = call("GET", "/api/admin/dashboard/summary", token=ctx.admin)
    for q in (0, 4, 5):
        ctx.plant(quantity=q)
    s, b = call("GET", "/api/admin/dashboard/summary", token=ctx.admin)
    bp, ap = before["data"]["plants"], b["data"]["plants"]
    return verify(s, b, 200, checks=[(f"total +3 (was {bp['total']}, now {ap['total']})",
                                      lambda: ap["total"] - bp["total"] == 3),
                                     (f"lowStock +2 (was {bp['lowStock']}, now {ap['lowStock']})",
                                      lambda: ap["lowStock"] - bp["lowStock"] == 2)])


@api_test("TC_API_M1_10", 'M1', "A category cannot be its own parent (Edit)", "PUT /api/admin/categories/{id}", 'Admin token',
          'id = main category C; {"name":"<C name>","parentId":<C id>}',
          '400 Bad Request, errors.parentId = "A category cannot be its own parent"',
          precondition="A main category C exists.")
def _(ctx):
    cat = ctx.main_cat()
    s, b = call("PUT", f"/api/admin/categories/{cat['id']}", {"name": cat["name"], "parentId": cat["id"]}, ctx.admin)
    return verify(s, b, 400, field="parentId", field_msg="A category cannot be its own parent")


@api_test("TC_API_M1_11", 'M1', "Delete sub-category with 2 plants shows plural message", "DELETE /api/admin/categories/{id}",
          'Admin token', "id = sub-category that contains exactly 2 plants",
          '409 Conflict, message "Category cannot be deleted because it has 2 plants."',
          precondition="A sub-category with exactly two plants exists.")
def _(ctx):
    sub = ctx.sub_cat()
    ctx.plant(category_id=sub["id"])
    ctx.plant(category_id=sub["id"])
    s, b = call("DELETE", f"/api/admin/categories/{sub['id']}", token=ctx.admin)
    return verify(s, b, 409, "Category cannot be deleted because it has 2 plants.")


@api_test("TC_API_M1_12", 'M1', "Main category with sub-categories cannot be moved under another", "PUT /api/admin/categories/{id}",
          'Admin token', 'id = main M (has 1 sub-category); {"name":"<M name>","parentId":<other main id>}',
          '400 Bad Request, errors.parentId = "A category with sub-categories cannot be moved under another category"',
          precondition="Main category M with one sub-category, and another main category O, exist.")
def _(ctx):
    m, other = ctx.main_cat(), ctx.main_cat()
    ctx.sub_cat(m["id"])
    s, b = call("PUT", f"/api/admin/categories/{m['id']}", {"name": m["name"], "parentId": other["id"]}, ctx.admin)
    return verify(s, b, 400, field="parentId",
                  field_msg="A category with sub-categories cannot be moved under another category")


@api_test("TC_API_M1_13", 'M1', "Category name with an accented letter is not a duplicate", 'POST /api/admin/categories', 'Admin token',
          'Category "Cafe<xyz>" exists; send {"name":"Café<xyz>","parentId":null}',
          '201 Created, "Category created successfully" - names are unique only case-insensitively (SRS 6.3.2), '
          'and "Café" is a different name from "Cafe"',
          precondition='A main category "Cafe<xyz>" exists.')
def _(ctx):
    u = ctx.uniq(3)
    call("POST", "/api/admin/categories", {"name": "Cafe" + u, "parentId": None}, ctx.admin)
    s, b = call("POST", "/api/admin/categories", {"name": "Café" + u, "parentId": None}, ctx.admin)
    return verify(s, b, 201, "Category created successfully")


@api_test("TC_API_M1_14", 'M1', "Parallel: 8 identical Add Category requests create only one category", 'POST /api/admin/categories',
          'Admin token', '8 x {"name":"<same unique name>","parentId":null} sent at the same moment',
          '1 x 201 "Category created successfully", 7 x 409 "Category name already exists"; '
          'GET /api/admin/categories?search=<name> returns 1 category (SRS 6.3.2 unique within the same parent)',
          steps="1. Prepare a new category name.\n2. Send POST /api/admin/categories 8 times at the same moment "
                "(Postman Runner, 8 iterations, 0 ms delay).\n3. Count the 201 and 409 responses.\n"
                "4. Send GET /api/admin/categories?search=<name> and count the rows.")
def _(ctx):
    name = "P" + ctx.uniq(6)
    r = parallel(*[lambda: call("POST", "/api/admin/categories", {"name": name, "parentId": None}, ctx.admin)] * 8)
    s, b = call("GET", f"/api/admin/categories?search={name}", token=ctx.admin)
    codes = sorted(x[0] for x in r)
    return verify(s, b, 200, checks=[(f"exactly one 201 (got {codes})", lambda: codes.count(201) == 1),
                                     (f"one saved category (got {b['data']['totalElements']})", lambda: b["data"]["totalElements"] == 1)])


@api_test("TC_API_M1_15", 'M1', "Category name of 7 characters including emoji is within 3-10", 'POST /api/admin/categories', 'Admin token',
          '{"name":"<3 letters>🌵🌵🌵🌵","parentId":null}  (7 characters)',
          '201 Created, "Category created successfully" (SRS 6.3.2 "Length 3-10" counts characters)')
def _(ctx):
    name = ctx.uniq(3) + "🌵" * 4
    s, b = call("POST", "/api/admin/categories", {"name": name, "parentId": None}, ctx.admin)
    return verify(s, b, 201, "Category created successfully", checks=[("name is 7 characters", lambda: len(name) == 7)])
