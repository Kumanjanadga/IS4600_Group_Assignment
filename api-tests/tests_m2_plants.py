"""M2 - Plant Management (SRS 6.4)

Owner: M2. 15 API test cases. No login/logout cases (sir: no test cases for the login function).
Cases marked "Parallel" send the same request several times at the same moment (Postman Collection Runner, or
framework.parallel here). Defect IDs are listed in DEFECT_REPORT.md.
"""
from urllib.parse import quote  # noqa: F401
from client import call, login_client  # noqa: F401
from framework import api_test, verify, parallel  # noqa: F401
from helpers import plant_body, reg_body, post_reg, content, buy, sell  # noqa: F401


@api_test("TC_API_M2_01", 'M2', "Add a plant with valid data", 'POST /api/admin/plants', 'Admin token',
          '{"name":"<unique>","categoryId":<sub id>,"price":25.00,"quantity":10}',
          '201 Created, message "Plant created successfully", price 25.00, quantity 10', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    b0 = plant_body(ctx)
    s, b = call("POST", "/api/admin/plants", b0, ctx.admin)
    return verify(s, b, 201, "Plant created successfully",
                  checks=[("price 25.00", lambda: float(b["data"]["price"]) == 25.00),
                          ("quantity 10", lambda: b["data"]["quantity"] == 10)])


@api_test("TC_API_M2_02", 'M2', "Price at maximum boundary 10000.00 is accepted", 'POST /api/admin/plants', 'Admin token',
          'price = 10000.00 (other fields valid)', '201 Created, message "Plant created successfully"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=10000.00), ctx.admin)
    return verify(s, b, 201, "Plant created successfully")


@api_test("TC_API_M2_03", 'M2', "Price above maximum (10000.01) is rejected", 'POST /api/admin/plants', 'Admin token',
          'price = 10000.01', '400 Bad Request, errors.price = "Price cannot exceed 10000.00"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=10000.01), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price cannot exceed 10000.00")


@api_test("TC_API_M2_04", 'M2', "Price of 0 is rejected", 'POST /api/admin/plants', 'Admin token',
          'price = 0', '400 Bad Request, errors.price = "Price must be greater than 0"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=0), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price must be greater than 0")


@api_test("TC_API_M2_05", 'M2', "Price with 3 decimal places is rejected", 'POST /api/admin/plants', 'Admin token',
          'price = 12.345', '400 Bad Request, errors.price = "Price can have at most 2 decimal places"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=12.345), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price can have at most 2 decimal places")


@api_test("TC_API_M2_06", 'M2', "Trailing zeros do not count as decimals (10.500)", 'POST /api/admin/plants', 'Admin token',
          'price = "10.500" (sent as text)', '201 Created, price saved as 10.50', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price="10.500"), ctx.admin)
    return verify(s, b, 201, "Plant created successfully",
                  checks=[("price 10.50", lambda: float(b["data"]["price"]) == 10.50)])


@api_test("TC_API_M2_07", 'M2', "Negative quantity is rejected", 'POST /api/admin/plants', 'Admin token',
          'quantity = -1', '400 Bad Request, errors.quantity = "Quantity cannot be negative"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, quantity=-1), ctx.admin)
    return verify(s, b, 400, field="quantity", field_msg="Quantity cannot be negative")


@api_test("TC_API_M2_08", 'M2', "Plant cannot be added to a main category", 'POST /api/admin/plants', 'Admin token',
          'categoryId = <main category id>', '400 Bad Request, errors.categoryId = "Category must be a sub-category"',
          "Admin is logged in; a main category exists.")
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, categoryId=ctx.main_cat()["id"]), ctx.admin)
    return verify(s, b, 400, field="categoryId", field_msg="Category must be a sub-category")


@api_test("TC_API_M2_09", 'M2', "Duplicate plant name (different case) is rejected", 'POST /api/admin/plants', 'Admin token',
          'name = existing plant name in UPPERCASE', '409 Conflict, "Plant name already exists"',
          "A plant already exists.")
def _(ctx):
    p = ctx.plant()
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, name=p["name"].upper()), ctx.admin)
    return verify(s, b, 409, checks=[("'Plant name already exists' in response",
                                      lambda: "Plant name already exists" in str(b))])


@api_test("TC_API_M2_10", 'M2', "Plant name above maximum length (26 chars)", 'POST /api/admin/plants', 'Admin token',
          'name = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" (26 chars)',
          '400 Bad Request, errors.name = "Plant name must be between 3 and 25 characters"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, name="ABCDEFGHIJKLMNOPQRSTUVWXYZ"), ctx.admin)
    return verify(s, b, 400, field="name", field_msg="Plant name must be between 3 and 25 characters")


@api_test("TC_API_M2_11", 'M2', "Plant with sales records cannot be deleted",
          "DELETE /api/admin/plants/{id}", 'Admin token', "id = plant that has 1 sale",
          '409 Conflict, message "Plant cannot be deleted because it has sales records."',
          "A plant with at least one sale exists.")
def _(ctx):
    p = ctx.plant(quantity=5)
    ctx.sell(p["id"], 1)
    s, b = call("DELETE", f"/api/admin/plants/{p['id']}", token=ctx.admin)
    return verify(s, b, 409, "Plant cannot be deleted because it has sales records.")


@api_test("TC_API_M2_12", 'M2', "Filter by main category returns plants of all its sub-categories",
          "GET /api/admin/plants?categoryId={mainId}", 'Admin token',
          "Main category with 2 sub-categories, 1 plant in each",
          "200 OK, list contains both plants (totalElements = 2)",
          "A main category with two sub-categories, each with one plant.")
def _(ctx):
    main = ctx.main_cat()
    p1 = ctx.plant(category_id=ctx.sub_cat(main["id"])["id"])
    p2 = ctx.plant(category_id=ctx.sub_cat(main["id"])["id"])
    s, b = call("GET", f"/api/admin/plants?categoryId={main['id']}", token=ctx.admin)
    ids = lambda: {x["id"] for x in b["data"]["content"]}  # noqa: E731
    return verify(s, b, 200, checks=[("both plants returned", lambda: ids() == {p1["id"], p2["id"]})])


@api_test("TC_API_M2_13", 'M2', "Parallel: sub-category made main while plants are added keeps plants in sub-categories only",
          "PUT /api/admin/categories/{id}", 'Admin token',
          'At the same moment: PUT /api/admin/categories/{S} {"name":"<S>","parentId":null} and '
          '3 x POST /api/admin/plants {"name":"<new>","categoryId":<S>,"price":5,"quantity":7}',
          'One side is rejected; afterwards S is never a main category that holds plants (SRS 6.3.2 "A sub-category that has '
          'plants cannot be changed into a main category", 6.4.2 "Category must be a sub-category")',
          precondition="A sub-category S without plants exists.",
          steps="1. Send the PUT (make S a main category) and three POST /api/admin/plants into S at the same moment.\n"
                "2. Send GET /api/admin/categories/{S} and GET /api/admin/plants?categoryId={S}.\n"
                "3. Check that S is not a main category with plants.")
def _(ctx):
    s2 = ctx.sub_cat()

    def mk():
        return call("POST", "/api/admin/plants", {"name": "MP " + ctx.uniq(7), "categoryId": s2["id"], "price": 5, "quantity": 7}, ctx.admin)
    r = parallel(lambda: call("PUT", f"/api/admin/categories/{s2['id']}", {"name": s2["name"], "parentId": None}, ctx.admin), mk, mk, mk)
    s, b = call("GET", f"/api/admin/categories/{s2['id']}", token=ctx.admin)
    n = call("GET", f"/api/admin/plants?categoryId={s2['id']}", token=ctx.admin)[1]["data"]["totalElements"]
    is_main = b["data"]["parentId"] is None
    return verify(s, b, 200, checks=[(f"not a main category with plants (main={is_main}, plants={n}, statuses {[x[0] for x in r]})",
                                      lambda: not (is_main and n))])


@api_test("TC_API_M2_14", 'M2', "Stock never becomes negative when a sale is deleted at maximum stock",
          "DELETE /api/admin/sales/{id}", 'Admin token',
          "Plant qty 10 -> sell 5 -> edit plant quantity to 2147483647 -> delete the sale",
          'Stock is never negative (SRS 6.5.2 "stock can never become negative"): the delete is rejected or the stock '
          'stays >= 0; GET /api/admin/plants/{id} quantity >= 0',
          precondition="A plant with quantity 10 exists.",
          steps="1. Send POST /api/admin/sales {plantId, quantity 5}.\n2. Send PUT /api/admin/plants/{id} with quantity 2147483647.\n"
                "3. Send DELETE /api/admin/sales/{saleId}.\n4. Send GET /api/admin/plants/{id} and check quantity.")
def _(ctx):
    p = ctx.plant(quantity=10)
    sale = ctx.sell(p["id"], 5)
    call("PUT", f"/api/admin/plants/{p['id']}", {"name": p["name"], "categoryId": p["categoryId"], "price": 25, "quantity": 2147483647}, ctx.admin)
    s, b = call("DELETE", f"/api/admin/sales/{sale['id']}", token=ctx.admin)
    q = ctx.get_plant(p["id"])["quantity"]
    return verify(s, b, s, checks=[(f"stock not negative (stock={q})", lambda: q >= 0)])


@api_test("TC_API_M2_15", 'M2', "Two invalid fields: price 0 AND category not found", 'POST /api/admin/plants', 'Admin token',
          '{"name":"Okay Plant <x>","categoryId":999999,"price":0,"quantity":1}',
          '400 Bad Request with one message per field (SRS 4.7): errors.price = "Price must be greater than 0" AND '
          'errors.categoryId = "Category not found"')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", {"name": "Okay " + ctx.uniq(6), "categoryId": 999999, "price": 0, "quantity": 1}, ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price must be greater than 0",
                  checks=[("errors.categoryId = 'Category not found'",
                           lambda: (b.get("errors") or {}).get("categoryId") == "Category not found")])
