"""M2 - Plant Management (SRS 6.4)

Owner: M2. 15 API test cases. No login/logout cases (sir: no test cases for the login function).
Cases marked "Parallel" send the same request several times at the same moment (Postman Collection Runner, or
framework.parallel here). Defect IDs are listed in DEFECT_REPORT.md.
"""
from urllib.parse import quote  # noqa: F401
from client import call, login_client  # noqa: F401
from framework import api_test, verify, parallel  # noqa: F401
from helpers import plant_body, reg_body, post_reg, content, buy, sell  # noqa: F401


@api_test("ADM-PLT-API-01", 'M2', "Add a plant with valid data", 'POST /api/admin/plants', 'Admin token',
          '{"name":"<unique>","categoryId":<sub id>,"price":25.00,"quantity":10}',
          '201 Created, message "Plant created successfully", price 25.00, quantity 10', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    b0 = plant_body(ctx)
    s, b = call("POST", "/api/admin/plants", b0, ctx.admin)
    return verify(s, b, 201, "Plant created successfully",
                  checks=[("price 25.00", lambda: float(b["data"]["price"]) == 25.00),
                          ("quantity 10", lambda: b["data"]["quantity"] == 10)])


@api_test("ADM-PLT-API-02", 'M2', "Price at maximum boundary 10000.00 is accepted", 'POST /api/admin/plants', 'Admin token',
          'price = 10000.00 (other fields valid)', '201 Created, message "Plant created successfully"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=10000.00), ctx.admin)
    return verify(s, b, 201, "Plant created successfully")


@api_test("ADM-PLT-API-03", 'M2', "Price above maximum (10000.01) is rejected", 'POST /api/admin/plants', 'Admin token',
          'price = 10000.01', '400 Bad Request, errors.price = "Price cannot exceed 10000.00"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=10000.01), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price cannot exceed 10000.00")


@api_test("ADM-PLT-API-04", 'M2', "Price of 0 is rejected", 'POST /api/admin/plants', 'Admin token',
          'price = 0', '400 Bad Request, errors.price = "Price must be greater than 0"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=0), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price must be greater than 0")


@api_test("ADM-PLT-API-05", 'M2', "Price with 3 decimal places is rejected", 'POST /api/admin/plants', 'Admin token',
          'price = 12.345', '400 Bad Request, errors.price = "Price can have at most 2 decimal places"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price=12.345), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price can have at most 2 decimal places")


@api_test("ADM-PLT-API-06", 'M2', "Trailing zeros do not count as decimals (10.500)", 'POST /api/admin/plants', 'Admin token',
          'price = "10.500" (sent as text)', '201 Created, price saved as 10.50', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, price="10.500"), ctx.admin)
    return verify(s, b, 201, "Plant created successfully",
                  checks=[("price 10.50", lambda: float(b["data"]["price"]) == 10.50)])


@api_test("ADM-PLT-API-07", 'M2', "Negative quantity is rejected", 'POST /api/admin/plants', 'Admin token',
          'quantity = -1', '400 Bad Request, errors.quantity = "Quantity cannot be negative"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, quantity=-1), ctx.admin)
    return verify(s, b, 400, field="quantity", field_msg="Quantity cannot be negative")


@api_test("ADM-PLT-API-08", 'M2', "Plant cannot be added to a main category", 'POST /api/admin/plants', 'Admin token',
          'categoryId = <main category id>', '400 Bad Request, errors.categoryId = "Category must be a sub-category"',
          "Admin is logged in; a main category exists.")
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, categoryId=ctx.main_cat()["id"]), ctx.admin)
    return verify(s, b, 400, field="categoryId", field_msg="Category must be a sub-category")


@api_test("ADM-PLT-API-09", 'M2', "Duplicate plant name (different case) is rejected", 'POST /api/admin/plants', 'Admin token',
          'name = existing plant name in UPPERCASE', '409 Conflict, "Plant name already exists"',
          "A plant already exists.")
def _(ctx):
    p = ctx.plant()
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, name=p["name"].upper()), ctx.admin)
    return verify(s, b, 409, checks=[("'Plant name already exists' in response",
                                      lambda: "Plant name already exists" in str(b))])


@api_test("ADM-PLT-API-10", 'M2', "Plant name above maximum length (26 chars)", 'POST /api/admin/plants', 'Admin token',
          'name = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" (26 chars)',
          '400 Bad Request, errors.name = "Plant name must be between 3 and 25 characters"', 'Admin is logged in; a sub-category exists.')
def _(ctx):
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, name="ABCDEFGHIJKLMNOPQRSTUVWXYZ"), ctx.admin)
    return verify(s, b, 400, field="name", field_msg="Plant name must be between 3 and 25 characters")


@api_test("ADM-PLT-API-11", 'M2', "Plant with sales records cannot be deleted",
          "DELETE /api/admin/plants/{id}", 'Admin token', "id = plant that has 1 sale",
          '409 Conflict, message "Plant cannot be deleted because it has sales records."',
          "A plant with at least one sale exists.")
def _(ctx):
    p = ctx.plant(quantity=5)
    ctx.sell(p["id"], 1)
    s, b = call("DELETE", f"/api/admin/plants/{p['id']}", token=ctx.admin)
    return verify(s, b, 409, "Plant cannot be deleted because it has sales records.")


@api_test("ADM-PLT-API-12", 'M2', "Filter by main category returns plants of all its sub-categories",
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


@api_test("ADM-PLT-API-13", 'M2', "Plant name with a special letter is not a duplicate", 'POST /api/admin/plants', 'Admin token',
          'Plant "Straße Fern <xyz>" exists; send {"name":"Strasse Fern <xyz>","categoryId":<sub id>,"price":5,"quantity":5}',
          '201 Created, "Plant created successfully" - plant names are unique only case-insensitively (SRS 6.4.2), '
          'and "Strasse" is a different name from "Straße"',
          precondition='A sub-category and a plant "Straße Fern <xyz>" exist.')
def _(ctx):
    sub = ctx.sub_cat()["id"]
    u = ctx.uniq(4)
    call("POST", "/api/admin/plants", {"name": f"Straße Fern {u}", "categoryId": sub, "price": 5, "quantity": 5}, ctx.admin)
    s, b = call("POST", "/api/admin/plants", {"name": f"Strasse Fern {u}", "categoryId": sub, "price": 5, "quantity": 5}, ctx.admin)
    return verify(s, b, 201, "Plant created successfully")


@api_test("ADM-PLT-API-14", 'M2', "Stock never becomes negative when a sale is deleted at maximum stock",
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


@api_test("ADM-PLT-API-15", 'M2', "Plant name of 20 characters including emoji is within 3-25", 'POST /api/admin/plants', 'Admin token',
          '{"name":"Rose<4 letters>🌹🌹🌹🌹🌹🌹🌹🌹🌹🌹🌹🌹","categoryId":<sub id>,"price":5,"quantity":1}  (20 characters)',
          '201 Created, "Plant created successfully" (SRS 6.4.2 "Length 3-25" counts characters)',
          precondition="A sub-category exists.")
def _(ctx):
    name = "Rose" + ctx.uniq(4) + "🌹" * 12
    s, b = call("POST", "/api/admin/plants", plant_body(ctx, name=name), ctx.admin)
    return verify(s, b, 201, "Plant created successfully", checks=[("name is 20 characters", lambda: len(name) == 20)])
