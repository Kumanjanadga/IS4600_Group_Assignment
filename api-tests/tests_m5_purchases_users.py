"""M5 - Buy Plant + My Purchases (SRS 7.5, 7.6) + User Management (SRS 6.6)

Owner: M5. 15 API test cases. No login/logout cases (sir: no test cases for the login function).
Cases marked "Parallel" send the same request several times at the same moment (Postman Collection Runner, or
framework.parallel here). Defect IDs are listed in DEFECT_REPORT.md.
"""
from urllib.parse import quote  # noqa: F401
from client import call, login_client  # noqa: F401
from framework import api_test, verify, parallel  # noqa: F401
from helpers import plant_body, reg_body, post_reg, content, buy, sell  # noqa: F401


@api_test("TC_API_M5_01", 'M5', "Client buys a plant and stock is reduced", 'POST /api/client/purchases', 'Client token',
          '{"plantId":<plant with stock 10, price 25.00>,"quantity":2}',
          '201 Created, message "Purchase completed successfully.", totalPrice 50.00, plant stock becomes 8', 'A Client is logged in; a plant with stock exists.')
def _(ctx):
    p = ctx.plant(quantity=10, price=25.00)
    s, b = buy(ctx.client, p["id"], 2)
    return verify(s, b, 201, "Purchase completed successfully.",
                  checks=[("total 50.00", lambda: float(b["data"]["totalPrice"]) == 50.0),
                          ("stock 8", lambda: ctx.get_plant(p["id"])["quantity"] == 8)])


@api_test("TC_API_M5_02", 'M5', "Purchase quantity 0 is rejected", 'POST /api/client/purchases', 'Client token', '{"plantId":<id>,"quantity":0}',
          '400 Bad Request, errors.quantity = "Quantity must be greater than 0"', 'A Client is logged in; a plant with stock exists.')
def _(ctx):
    p = ctx.plant()
    s, b = buy(ctx.client, p["id"], 0)
    return verify(s, b, 400, field="quantity", field_msg="Quantity must be greater than 0")


@api_test("TC_API_M5_03", 'M5', "Purchase quantity above stock is rejected, stock unchanged", 'POST /api/client/purchases', 'Client token',
          '{"plantId":<plant with stock 3>,"quantity":4}',
          '400 Bad Request, "Only 3 items available in stock"; plant stock remains 3',
          "A Client is logged in; a plant with stock 3 exists.")
def _(ctx):
    p = ctx.plant(quantity=3)
    s, b = buy(ctx.client, p["id"], 4)
    return verify(s, b, 400, checks=[("message", lambda: "Only 3 items available in stock" in str(b)),
                                     ("stock 3", lambda: ctx.get_plant(p["id"])["quantity"] == 3)])


@api_test("TC_API_M5_04", 'M5', "Buying an out-of-stock plant is rejected", 'POST /api/client/purchases', 'Client token',
          '{"plantId":<plant with stock 0>,"quantity":1}', '409 Conflict, "This plant is out of stock"',
          "A Client is logged in; a plant with stock 0 exists.")
def _(ctx):
    p = ctx.plant(quantity=0)
    s, b = buy(ctx.client, p["id"], 1)
    return verify(s, b, 409, checks=[("message", lambda: "This plant is out of stock" in str(b))])


@api_test("TC_API_M5_05", 'M5', "Buying a non-existing plant", 'POST /api/client/purchases', 'Client token', '{"plantId":99999999,"quantity":1}',
          '400 Bad Request, errors.plantId = "Plant not found" (field rule "Plant must exist", SRS 6.5.2/4.7)',
          "A Client is logged in.")
def _(ctx):
    s, b = buy(ctx.client, 99999999, 1)
    return verify(s, b, 400, field="plantId", field_msg="Plant not found")


@api_test("TC_API_M5_06", 'M5', "Decimal purchase quantity is rejected", 'POST /api/client/purchases', 'Client token', '{"plantId":<id>,"quantity":1.5}',
          '400 Bad Request, errors.quantity = "Quantity must be a whole number"', 'A Client is logged in; a plant with stock exists.')
def _(ctx):
    p = ctx.plant()
    s, b = buy(ctx.client, p["id"], 1.5)
    return verify(s, b, 400, field="quantity", field_msg="Quantity must be a whole number")


@api_test("TC_API_M5_07", 'M5', "My Purchases shows only the logged-in Client's purchases",
          "GET /api/client/purchases", "Client A token",
          "Client A buys plant X; Client B buys plant Y; Client A lists purchases",
          "200 OK, list contains plant X and not plant Y", "Two Clients exist and each has bought a plant.")
def _(ctx):
    a, c = ctx.new_client(), ctx.new_client()
    px, py = ctx.plant(), ctx.plant()
    ctx.buy(a["token"], px["id"])
    ctx.buy(c["token"], py["id"])
    s, b = call("GET", "/api/client/purchases?size=100", token=a["token"])
    ids = lambda: [x["plantId"] for x in b["data"]["content"]]  # noqa: E731
    return verify(s, b, 200, checks=[("own purchase listed", lambda: px["id"] in ids()),
                                     ("other client's purchase hidden", lambda: py["id"] not in ids())])


@api_test("TC_API_M5_08", 'M5', "Purchase keeps the unit price at the time of purchase",
          "GET /api/client/purchases", 'Client token',
          "Buy plant at 20.00; Admin changes price to 35.00; list purchases",
          "200 OK, purchase still shows unitPrice 20.00", 'A Client is logged in; a plant with stock exists.')
def _(ctx):
    cl = ctx.new_client()
    p = ctx.plant(price=20.00)
    ctx.buy(cl["token"], p["id"], 1)
    call("PUT", f"/api/admin/plants/{p['id']}", {"name": p["name"], "categoryId": p["categoryId"],
                                                  "price": 35.00, "quantity": p["quantity"] - 1}, ctx.admin)
    s, b = call("GET", "/api/client/purchases", token=cl["token"])
    return verify(s, b, 200, checks=[("unitPrice 20.00", lambda: float(b["data"]["content"][0]["unitPrice"]) == 20.0)])


@api_test("TC_API_M5_09", 'M5', "Token of a deactivated Client is rejected", "GET /api/client/purchases",
          "Token of a Client later deactivated", "Client logs in; Admin deactivates the Client; Client lists purchases",
          '401 Unauthorized, message "Your account is inactive. Please contact support."',
          "A Client is logged in.")
def _(ctx):
    cl = ctx.new_client()
    call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    s, b = call("GET", "/api/client/purchases", token=cl["token"])
    return verify(s, b, 401, "Your account is inactive. Please contact support.")


@api_test("TC_API_M5_10", 'M5', "Deactivate an active Client", "PATCH /api/admin/users/{id}/deactivate", 'Admin token',
          "id = active Client", '200 OK, message "User deactivated successfully.", status INACTIVE',
          "An active Client exists.")
def _(ctx):
    cl = ctx.new_client(login=False)
    s, b = call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    return verify(s, b, 200, "User deactivated successfully.",
                  checks=[("status INACTIVE", lambda: b["data"]["status"] == "INACTIVE")])


@api_test("TC_API_M5_11", 'M5', "Deactivating an already inactive Client is rejected",
          "PATCH /api/admin/users/{id}/deactivate", 'Admin token', "id = inactive Client",
          '409 Conflict, message "User is already inactive"', "An inactive Client exists.")
def _(ctx):
    cl = ctx.new_client(login=False)
    call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    s, b = call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    return verify(s, b, 409, "User is already inactive")


@api_test("TC_API_M5_12", 'M5', "Admin account cannot be deactivated", "PATCH /api/admin/users/{id}/deactivate",
          'Admin token', "id = 1 (the admin account)", '404 Not Found, message "User not found"', "Admin is logged in.")
def _(ctx):
    s, b = call("PATCH", "/api/admin/users/1/deactivate", token=ctx.admin)
    return verify(s, b, 404, "User not found")


@api_test("TC_API_M5_13", 'M5', "Old token stays invalid after the Client is reactivated",
          "PATCH /api/admin/users/{id}/activate", 'Admin token',
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


@api_test("TC_API_M5_14", 'M5', "Parallel: deactivating the same Client twice succeeds only once",
          "PATCH /api/admin/users/{id}/deactivate", 'Admin token', "6 x PATCH .../deactivate for one active Client, at the same moment",
          '1 x 200 "User deactivated successfully.", 5 x 409 "User is already inactive" (SRS 6.6.2)',
          precondition="An active Client exists.",
          steps="1. Send PATCH /api/admin/users/{id}/deactivate 6 times at the same moment (Postman Runner, 6 iterations).\n"
                "2. Count the 200 and 409 responses.")
def _(ctx):
    cl = ctx.new_client(login=False)
    r = parallel(*[lambda: call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)] * 6)
    codes = sorted(x[0] for x in r)
    s, b = r[0]
    return verify(s, b, s, checks=[(f"1 x 200 and 5 x 409 (got {codes})", lambda: codes == [200, 409, 409, 409, 409, 409])])


@api_test("TC_API_M5_15", 'M5', "Two invalid fields: out-of-stock plant AND quantity 0", 'POST /api/client/purchases', 'Client token',
          '{"plantId":<plant with stock 0>,"quantity":0}',
          '400 with one message per field (SRS 4.7, 7.5 table): errors.quantity = "Quantity must be greater than 0" AND '
          'the plant error "This plant is out of stock"', precondition="A Client is logged in; a plant with stock 0 exists.")
def _(ctx):
    p = ctx.plant(quantity=0)
    s, b = buy(ctx.client, p["id"], 0)
    return verify(s, b, 400, field="quantity", field_msg="Quantity must be greater than 0",
                  checks=[("errors.plantId = 'This plant is out of stock'",
                           lambda: (b.get("errors") or {}).get("plantId") == "This plant is out of stock")])
