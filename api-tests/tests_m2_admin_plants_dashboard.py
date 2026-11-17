"""M2 - Plant Management + Dashboard (SRS 6.2, 6.4, 4.7)."""
from client import call
from framework import api_test, verify

M = "M2"
ADD = "POST /api/admin/plants"
ADMIN = "Admin token"
PRE = "Admin is logged in; a sub-category exists."


def body(ctx, **over):
    b = {"name": "Plant " + ctx.uniq(8), "categoryId": ctx.sub_cat()["id"], "price": 25.00, "quantity": 10}
    b.update(over)
    return b


@api_test("TC_API_M2_01", M, "Add a plant with valid data", ADD, ADMIN,
          '{"name":"<unique>","categoryId":<sub id>,"price":25.00,"quantity":10}',
          '201 Created, message "Plant created successfully", price 25.00, quantity 10', PRE)
def _(ctx):
    b0 = body(ctx)
    s, b = call("POST", "/api/admin/plants", b0, ctx.admin)
    return verify(s, b, 201, "Plant created successfully",
                  checks=[("price 25.00", lambda: float(b["data"]["price"]) == 25.00),
                          ("quantity 10", lambda: b["data"]["quantity"] == 10)])


@api_test("TC_API_M2_02", M, "Price at maximum boundary 10000.00 is accepted", ADD, ADMIN,
          'price = 10000.00 (other fields valid)', '201 Created, message "Plant created successfully"', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, price=10000.00), ctx.admin)
    return verify(s, b, 201, "Plant created successfully")


@api_test("TC_API_M2_03", M, "Price above maximum (10000.01) is rejected", ADD, ADMIN,
          'price = 10000.01', '400 Bad Request, errors.price = "Price cannot exceed 10000.00"', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, price=10000.01), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price cannot exceed 10000.00")


@api_test("TC_API_M2_04", M, "Price of 0 is rejected", ADD, ADMIN,
          'price = 0', '400 Bad Request, errors.price = "Price must be greater than 0"', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, price=0), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price must be greater than 0")


@api_test("TC_API_M2_05", M, "Price with 3 decimal places is rejected", ADD, ADMIN,
          'price = 12.345', '400 Bad Request, errors.price = "Price can have at most 2 decimal places"', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, price=12.345), ctx.admin)
    return verify(s, b, 400, field="price", field_msg="Price can have at most 2 decimal places")


@api_test("TC_API_M2_06", M, "Trailing zeros do not count as decimals (10.500)", ADD, ADMIN,
          'price = "10.500" (sent as text)', '201 Created, price saved as 10.50', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, price="10.500"), ctx.admin)
    return verify(s, b, 201, "Plant created successfully",
                  checks=[("price 10.50", lambda: float(b["data"]["price"]) == 10.50)])


@api_test("TC_API_M2_07", M, "Negative quantity is rejected", ADD, ADMIN,
          'quantity = -1', '400 Bad Request, errors.quantity = "Quantity cannot be negative"', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, quantity=-1), ctx.admin)
    return verify(s, b, 400, field="quantity", field_msg="Quantity cannot be negative")


@api_test("TC_API_M2_08", M, "Decimal quantity is rejected", ADD, ADMIN,
          'quantity = 2.5', '400 Bad Request, errors.quantity = "Quantity must be a whole number"', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, quantity=2.5), ctx.admin)
    return verify(s, b, 400, field="quantity", field_msg="Quantity must be a whole number")


@api_test("TC_API_M2_09", M, "Plant cannot be added to a main category", ADD, ADMIN,
          'categoryId = <main category id>', '400 Bad Request, errors.categoryId = "Category must be a sub-category"',
          "Admin is logged in; a main category exists.")
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, categoryId=ctx.main_cat()["id"]), ctx.admin)
    return verify(s, b, 400, field="categoryId", field_msg="Category must be a sub-category")


@api_test("TC_API_M2_10", M, "Duplicate plant name (different case) is rejected", ADD, ADMIN,
          'name = existing plant name in UPPERCASE', '409 Conflict, "Plant name already exists"',
          "A plant already exists.")
def _(ctx):
    p = ctx.plant()
    s, b = call("POST", "/api/admin/plants", body(ctx, name=p["name"].upper()), ctx.admin)
    return verify(s, b, 409, checks=[("'Plant name already exists' in response",
                                      lambda: "Plant name already exists" in str(b))])


@api_test("TC_API_M2_11", M, "Plant name above maximum length (26 chars)", ADD, ADMIN,
          'name = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" (26 chars)',
          '400 Bad Request, errors.name = "Plant name must be between 3 and 25 characters"', PRE)
def _(ctx):
    s, b = call("POST", "/api/admin/plants", body(ctx, name="ABCDEFGHIJKLMNOPQRSTUVWXYZ"), ctx.admin)
    return verify(s, b, 400, field="name", field_msg="Plant name must be between 3 and 25 characters")


@api_test("TC_API_M2_12", M, "Plant with sales records cannot be deleted",
          "DELETE /api/admin/plants/{id}", ADMIN, "id = plant that has 1 sale",
          '409 Conflict, message "Plant cannot be deleted because it has sales records."',
          "A plant with at least one sale exists.")
def _(ctx):
    p = ctx.plant(quantity=5)
    ctx.sell(p["id"], 1)
    s, b = call("DELETE", f"/api/admin/plants/{p['id']}", token=ctx.admin)
    return verify(s, b, 409, "Plant cannot be deleted because it has sales records.")


@api_test("TC_API_M2_13", M, "Filter by main category returns plants of all its sub-categories",
          "GET /api/admin/plants?categoryId={mainId}", ADMIN,
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


@api_test("TC_API_M2_14", M, "Dashboard low-stock count includes quantity 0 and 4, not 5",
          "GET /api/admin/dashboard/summary", ADMIN,
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


@api_test("TC_API_M2_15", M, "Plant list without token is rejected", "GET /api/admin/plants", "No token",
          "No Authorization header", '401 Unauthorized, message "Authentication required"')
def _(ctx):
    s, b = call("GET", "/api/admin/plants")
    return verify(s, b, 401, "Authentication required")
