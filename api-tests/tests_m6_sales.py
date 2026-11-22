"""M6 - Sales Management + Sell Plant (SRS 6.5)

Owner: M6. 15 API test cases. No login/logout cases (sir: no test cases for the login function).
Cases marked "Parallel" send the same request several times at the same moment (Postman Collection Runner, or
framework.parallel here). Defect IDs are listed in DEFECT_REPORT.md.
"""
from urllib.parse import quote  # noqa: F401
from client import call, login_client  # noqa: F401
from framework import api_test, verify, parallel  # noqa: F401
from helpers import plant_body, reg_body, post_reg, content, buy, sell  # noqa: F401


@api_test("ADM-SAL-API-01", 'M6', "Admin sells a plant; customer is 'Admin' and stock reduced", 'POST /api/admin/sales', 'Admin token',
          '{"plantId":<plant stock 10, price 15.00>,"quantity":3}',
          '201 Created, message "Sale completed successfully", customer "Admin", totalPrice 45.00, stock 7', 'Admin is logged in; a plant with stock exists.')
def _(ctx):
    p = ctx.plant(quantity=10, price=15.00)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 3})
    return verify(s, b, 201, "Sale completed successfully",
                  checks=[("customer Admin", lambda: b["data"]["customer"] == "Admin"),
                          ("total 45.00", lambda: float(b["data"]["totalPrice"]) == 45.0),
                          ("stock 7", lambda: ctx.get_plant(p["id"])["quantity"] == 7)])


@api_test("ADM-SAL-API-02", 'M6', "Sale quantity above stock is rejected, stock unchanged", 'POST /api/admin/sales', 'Admin token',
          '{"plantId":<plant stock 2>,"quantity":5}',
          '400 Bad Request, "Only 2 items available in stock"; stock remains 2',
          "Admin is logged in; a plant with stock 2 exists.")
def _(ctx):
    p = ctx.plant(quantity=2)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 5})
    return verify(s, b, 400, checks=[("message", lambda: "Only 2 items available in stock" in str(b)),
                                     ("stock 2", lambda: ctx.get_plant(p["id"])["quantity"] == 2)])


@api_test("ADM-SAL-API-03", 'M6', "Sale without quantity is rejected", 'POST /api/admin/sales', 'Admin token', '{"plantId":<id>}',
          '400 Bad Request, errors.quantity = "Quantity is required"', 'Admin is logged in; a plant with stock exists.')
def _(ctx):
    p = ctx.plant()
    s, b = sell(ctx, {"plantId": p["id"]})
    return verify(s, b, 400, field="quantity", field_msg="Quantity is required")


@api_test("ADM-SAL-API-04", 'M6', "Selling an out-of-stock plant is rejected", 'POST /api/admin/sales', 'Admin token',
          '{"plantId":<plant stock 0>,"quantity":1}', '409 Conflict, "This plant is out of stock"',
          "Admin is logged in; a plant with stock 0 exists.")
def _(ctx):
    p = ctx.plant(quantity=0)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 1})
    return verify(s, b, 409, checks=[("message", lambda: "This plant is out of stock" in str(b))])


@api_test("ADM-SAL-API-05", 'M6', "Sale without plantId is rejected", 'POST /api/admin/sales', 'Admin token', '{"quantity":1}',
          '400 Bad Request, errors.plantId = "Plant is required"', "Admin is logged in.")
def _(ctx):
    s, b = sell(ctx, {"quantity": 1})
    return verify(s, b, 400, field="plantId", field_msg="Plant is required")


@api_test("ADM-SAL-API-06", 'M6', "Deleting a sale restores the plant stock", "DELETE /api/admin/sales/{id}", 'Admin token',
          "Plant stock 10; sell 4 (stock 6); delete that sale",
          '200 OK, message "Sale deleted successfully", plant stock back to 10', 'Admin is logged in; a plant with stock exists.')
def _(ctx):
    p = ctx.plant(quantity=10)
    sale = ctx.sell(p["id"], 4)
    s, b = call("DELETE", f"/api/admin/sales/{sale['id']}", token=ctx.admin)
    return verify(s, b, 200, "Sale deleted successfully",
                  checks=[("stock 10", lambda: ctx.get_plant(p["id"])["quantity"] == 10)])


@api_test("ADM-SAL-API-07", 'M6', "Deleting a non-existing sale", "DELETE /api/admin/sales/{id}", 'Admin token',
          "id = 99999999", '404 Not Found, message "Sale not found"', "Admin is logged in.")
def _(ctx):
    s, b = call("DELETE", "/api/admin/sales/99999999", token=ctx.admin)
    return verify(s, b, 404, "Sale not found")


@api_test("ADM-SAL-API-08", 'M6', "Filter sales by customer type CLIENT",
          "GET /api/admin/sales?customerType=CLIENT", 'Admin token',
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


@api_test("ADM-SAL-API-09", 'M6', "soldFrom after soldTo is rejected",
          "GET /api/admin/sales?soldFrom=2026-11-20&soldTo=2026-11-10", 'Admin token',
          "soldFrom = 2026-11-20, soldTo = 2026-11-10",
          '400 Bad Request, "soldFrom must be on or before soldTo"', "Admin is logged in.")
def _(ctx):
    s, b = call("GET", "/api/admin/sales?soldFrom=2026-11-20&soldTo=2026-11-10", token=ctx.admin)
    return verify(s, b, 400, checks=[("message", lambda: "soldFrom must be on or before soldTo" in str(b))])


@api_test("ADM-SAL-API-10", 'M6', "Searching sales for 'admin' finds Admin sales",
          "GET /api/admin/sales?search=admin", 'Admin token', "search = ADMIN (upper case); at least one Admin sale exists",
          "200 OK, result contains sales with customer 'Admin'", "At least one Admin sale exists.")
def _(ctx):
    p = ctx.plant()
    sale = ctx.sell(p["id"], 1)
    s, b = call("GET", "/api/admin/sales?search=ADMIN&size=100", token=ctx.admin)
    return verify(s, b, 200, checks=[("admin sale found", lambda: sale["id"] in [r["id"] for r in b["data"]["content"]])])


@api_test("ADM-SAL-API-11", 'M6', "Sell exactly the whole stock", 'POST /api/admin/sales', 'Admin token',
          '{"plantId":<plant with stock 4>,"quantity":4}',
          '201 "Sale completed successfully"; plant stock becomes 0 and the plant is no longer in the Sell Plant dropdown '
          '(GET /api/admin/plants/in-stock)', precondition="A plant with stock 4 exists.")
def _(ctx):
    p = ctx.plant(quantity=4)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 4})
    ins = call("GET", "/api/admin/plants/in-stock", token=ctx.admin)[1]["data"]
    return verify(s, b, 201, "Sale completed successfully",
                  checks=[("stock 0", lambda: ctx.get_plant(p["id"])["quantity"] == 0),
                          ("not in Sell Plant dropdown", lambda: p["id"] not in [x["id"] for x in ins])])


@api_test("ADM-SAL-API-12", 'M6', "Deleting a Client purchase removes it from My Purchases and restores stock",
          "DELETE /api/admin/sales/{id}", 'Admin token', "Client buys 3 of a plant with stock 10; Admin deletes that sale",
          '200 "Sale deleted successfully"; the Client\'s GET /api/client/purchases no longer lists it; stock back to 10',
          precondition="A Client has bought 3 of a plant with stock 10.")
def _(ctx):
    cl = ctx.new_client()
    p = ctx.plant(quantity=10)
    pur = ctx.buy(cl["token"], p["id"], 3)
    s, b = call("DELETE", f"/api/admin/sales/{pur['id']}", token=ctx.admin)
    mine = call("GET", "/api/client/purchases", token=cl["token"])[1]["data"]["content"]
    return verify(s, b, 200, "Sale deleted successfully",
                  checks=[("removed from My Purchases", lambda: pur["id"] not in [x["id"] for x in mine]),
                          ("stock 10", lambda: ctx.get_plant(p["id"])["quantity"] == 10)])


@api_test("ADM-SAL-API-13", 'M6', "Parallel: deleting the same sale twice returns 404, not a server error",
          "DELETE /api/admin/sales/{id}", 'Admin token', "6 x DELETE /api/admin/sales/{id} of one sale, sent at the same moment",
          '1 x 200 "Sale deleted successfully", 5 x 404 "Sale not found" (SRS 4.6); no 500',
          precondition="One sale exists.",
          steps="1. Send DELETE /api/admin/sales/{id} 6 times at the same moment (Postman Runner, 6 iterations).\n"
                "2. Check every response status and message.")
def _(ctx):
    p = ctx.plant(quantity=10)
    sale = ctx.sell(p["id"], 4)
    r = parallel(*[lambda: call("DELETE", f"/api/admin/sales/{sale['id']}", token=ctx.admin)] * 6)
    codes = sorted(x[0] for x in r)
    bad = [x for x in r if x[0] not in (200, 404)]
    s, b = bad[0] if bad else r[0]
    return verify(s, b, s, checks=[(f"1 x 200 and 5 x 404, no 500 (got {codes})", lambda: codes == [200, 404, 404, 404, 404, 404])])


@api_test("ADM-SAL-API-14", 'M6', "Sold-date filter with To date 9999-12-31", "GET /api/admin/sales?soldTo=9999-12-31",
          'Admin token', "soldTo = 9999-12-31",
          '200 OK, "Sales retrieved successfully", all sales sold on or before that date (SRS 6.5.1 From/To both inclusive)')
def _(ctx):
    s, b = call("GET", "/api/admin/sales?soldTo=9999-12-31", token=ctx.admin)
    return verify(s, b, 200, "Sales retrieved successfully")


@api_test("ADM-SAL-API-15", 'M6', "Two invalid fields: out-of-stock plant AND quantity 0", 'POST /api/admin/sales', 'Admin token',
          '{"plantId":<plant with stock 0>,"quantity":0}',
          '400 with one message per field (SRS 4.7, 6.5.2 table): errors.quantity = "Quantity must be greater than 0" AND '
          'the plant error "This plant is out of stock"', precondition="A plant with stock 0 exists.")
def _(ctx):
    p = ctx.plant(quantity=0)
    s, b = sell(ctx, {"plantId": p["id"], "quantity": 0})
    return verify(s, b, 400, field="quantity", field_msg="Quantity must be greater than 0",
                  checks=[("errors.plantId = 'This plant is out of stock'",
                           lambda: (b.get("errors") or {}).get("plantId") == "This plant is out of stock")])
