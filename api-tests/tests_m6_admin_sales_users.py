"""M6 - Sales Management + User Management (SRS 6.5, 6.6, 4.2)."""
from urllib.parse import quote
from client import call
from framework import api_test, verify

M = "M6"
SELL = "POST /api/admin/sales"
ADMIN = "Admin token"
PRE = "Admin is logged in; a plant with stock exists."


def sell(ctx, body):
    return call("POST", "/api/admin/sales", body, ctx.admin)


@api_test("TC_API_M6_01", M, "Admin sells a plant; customer is 'Admin' and stock reduced", SELL, ADMIN,
          '{"plantId":<plant stock 10, price 15.00>,"quantity":3}',
          '201 Created, message "Sale completed successfully", customer "Admin", totalPrice 45.00, stock 7', PRE)
def _(ctx):
    p = ctx.plant(quantity=10, price=15.00)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 3})
    return verify(s, b, 201, "Sale completed successfully",
                  checks=[("customer Admin", lambda: b["data"]["customer"] == "Admin"),
                          ("total 45.00", lambda: float(b["data"]["totalPrice"]) == 45.0),
                          ("stock 7", lambda: ctx.get_plant(p["id"])["quantity"] == 7)])


@api_test("TC_API_M6_02", M, "Sale quantity above stock is rejected, stock unchanged", SELL, ADMIN,
          '{"plantId":<plant stock 2>,"quantity":5}',
          '400 Bad Request, "Only 2 items available in stock"; stock remains 2',
          "Admin is logged in; a plant with stock 2 exists.")
def _(ctx):
    p = ctx.plant(quantity=2)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 5})
    return verify(s, b, 400, checks=[("message", lambda: "Only 2 items available in stock" in str(b)),
                                     ("stock 2", lambda: ctx.get_plant(p["id"])["quantity"] == 2)])


@api_test("TC_API_M6_03", M, "Sale without quantity is rejected", SELL, ADMIN, '{"plantId":<id>}',
          '400 Bad Request, errors.quantity = "Quantity is required"', PRE)
def _(ctx):
    p = ctx.plant()
    s, b = sell(ctx, {"plantId": p["id"]})
    return verify(s, b, 400, field="quantity", field_msg="Quantity is required")


@api_test("TC_API_M6_04", M, "Selling an out-of-stock plant is rejected", SELL, ADMIN,
          '{"plantId":<plant stock 0>,"quantity":1}', '409 Conflict, "This plant is out of stock"',
          "Admin is logged in; a plant with stock 0 exists.")
def _(ctx):
    p = ctx.plant(quantity=0)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 1})
    return verify(s, b, 409, checks=[("message", lambda: "This plant is out of stock" in str(b))])


@api_test("TC_API_M6_05", M, "Sale without plantId is rejected", SELL, ADMIN, '{"quantity":1}',
          '400 Bad Request, errors.plantId = "Plant is required"', "Admin is logged in.")
def _(ctx):
    s, b = sell(ctx, {"quantity": 1})
    return verify(s, b, 400, field="plantId", field_msg="Plant is required")


@api_test("TC_API_M6_06", M, "Deleting a sale restores the plant stock", "DELETE /api/admin/sales/{id}", ADMIN,
          "Plant stock 10; sell 4 (stock 6); delete that sale",
          '200 OK, message "Sale deleted successfully", plant stock back to 10', PRE)
def _(ctx):
    p = ctx.plant(quantity=10)
    sale = ctx.sell(p["id"], 4)
    s, b = call("DELETE", f"/api/admin/sales/{sale['id']}", token=ctx.admin)
    return verify(s, b, 200, "Sale deleted successfully",
                  checks=[("stock 10", lambda: ctx.get_plant(p["id"])["quantity"] == 10)])


@api_test("TC_API_M6_07", M, "Deleting a non-existing sale", "DELETE /api/admin/sales/{id}", ADMIN,
          "id = 99999999", '404 Not Found, message "Sale not found"', "Admin is logged in.")
def _(ctx):
    s, b = call("DELETE", "/api/admin/sales/99999999", token=ctx.admin)
    return verify(s, b, 404, "Sale not found")


@api_test("TC_API_M6_08", M, "Filter sales by customer type CLIENT",
          "GET /api/admin/sales?customerType=CLIENT", ADMIN,
          "One Admin sale and one Client purchase of the same plant; filter CLIENT",
          "200 OK, every row has customerType CLIENT; the Client purchase is listed",
          "At least one Admin sale and one Client purchase exist.")
def _(ctx):
    cl = ctx.new_client()
    p = ctx.plant()
    ctx.sell(p["id"], 1)
    ctx.buy(cl["token"], p["id"], 1)
    s, b = call("GET", f"/api/admin/sales?customerType=CLIENT&search={quote(p['name'])}", token=ctx.admin)
    rows = lambda: b["data"]["content"]  # noqa: E731
    return verify(s, b, 200, checks=[("only CLIENT", lambda: rows() and all(r["customerType"] == "CLIENT" for r in rows())),
                                     ("client listed", lambda: cl["username"] in [r["customer"] for r in rows()])])


@api_test("TC_API_M6_09", M, "soldFrom after soldTo is rejected",
          "GET /api/admin/sales?soldFrom=2026-11-20&soldTo=2026-11-10", ADMIN,
          "soldFrom = 2026-11-20, soldTo = 2026-11-10",
          '400 Bad Request, "soldFrom must be on or before soldTo"', "Admin is logged in.")
def _(ctx):
    s, b = call("GET", "/api/admin/sales?soldFrom=2026-11-20&soldTo=2026-11-10", token=ctx.admin)
    return verify(s, b, 400, checks=[("message", lambda: "soldFrom must be on or before soldTo" in str(b))])


@api_test("TC_API_M6_10", M, "Searching sales for 'admin' finds Admin sales",
          "GET /api/admin/sales?search=admin", ADMIN, "search = ADMIN (upper case); at least one Admin sale exists",
          "200 OK, result contains sales with customer 'Admin'", "At least one Admin sale exists.")
def _(ctx):
    p = ctx.plant()
    sale = ctx.sell(p["id"], 1)
    s, b = call("GET", "/api/admin/sales?search=ADMIN&size=100", token=ctx.admin)
    return verify(s, b, 200, checks=[("admin sale found", lambda: sale["id"] in [r["id"] for r in b["data"]["content"]])])


@api_test("TC_API_M6_11", M, "User list shows Client accounts only", "GET /api/admin/users?size=100", ADMIN,
          "size = 100", '200 OK, message "Users retrieved successfully", no row with role ADMIN / username admin',
          "Admin is logged in.")
def _(ctx):
    s, b = call("GET", "/api/admin/users?size=100", token=ctx.admin)
    rows = lambda: b["data"]["content"]  # noqa: E731
    return verify(s, b, 200, "Users retrieved successfully",
                  checks=[("no admin rows", lambda: all(r["role"] == "CLIENT" and r["username"] != "admin" for r in rows()))])


@api_test("TC_API_M6_12", M, "Deactivate an active Client", "PATCH /api/admin/users/{id}/deactivate", ADMIN,
          "id = active Client", '200 OK, message "User deactivated successfully.", status INACTIVE',
          "An active Client exists.")
def _(ctx):
    cl = ctx.new_client(login=False)
    s, b = call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    return verify(s, b, 200, "User deactivated successfully.",
                  checks=[("status INACTIVE", lambda: b["data"]["status"] == "INACTIVE")])


@api_test("TC_API_M6_13", M, "Deactivating an already inactive Client is rejected",
          "PATCH /api/admin/users/{id}/deactivate", ADMIN, "id = inactive Client",
          '409 Conflict, message "User is already inactive"', "An inactive Client exists.")
def _(ctx):
    cl = ctx.new_client(login=False)
    call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    s, b = call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    return verify(s, b, 409, "User is already inactive")


@api_test("TC_API_M6_14", M, "Admin account cannot be deactivated", "PATCH /api/admin/users/{id}/deactivate",
          ADMIN, "id = 1 (the admin account)", '404 Not Found, message "User not found"', "Admin is logged in.")
def _(ctx):
    s, b = call("PATCH", "/api/admin/users/1/deactivate", token=ctx.admin)
    return verify(s, b, 404, "User not found")


@api_test("TC_API_M6_15", M, "Old token stays invalid after the Client is reactivated",
          "PATCH /api/admin/users/{id}/activate", ADMIN,
          "Client logs in (token T); Admin deactivates then activates the Client; call GET /api/client/me with T",
          'Activate 200 "User activated successfully."; call with T returns 401', "An active Client is logged in.",
          steps="1. Log in as a Client and keep token T.\n2. Admin sends PATCH .../deactivate for that Client.\n"
                "3. Admin sends PATCH .../activate for that Client.\n4. Send GET /api/client/me with token T.\n"
                "5. Check the activate response and the 401 status.")
def _(ctx):
    cl = ctx.new_client()
    call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    s1, b1 = call("PATCH", f"/api/admin/users/{cl['id']}/activate", token=ctx.admin)
    s, b = call("GET", "/api/client/me", token=cl["token"])
    return verify(s, b, 401, checks=[("activate 200", lambda: s1 == 200),
                                     ("activate message", lambda: b1.get("message") == "User activated successfully.")])
