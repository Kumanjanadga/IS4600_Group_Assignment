"""M5 - Buy Plant, My Purchases, Client account & session (SRS 7.5, 7.6, 4.2, 6.6.4)."""
from client import call, login_client
from framework import api_test, verify

M = "M5"
BUY = "POST /api/client/purchases"
CLIENT = "Client token"
PRE = "A Client is logged in; a plant with stock exists."


def buy(token, pid, qty):
    return call("POST", "/api/client/purchases", {"plantId": pid, "quantity": qty}, token)


@api_test("TC_API_M5_01", M, "Client buys a plant and stock is reduced", BUY, CLIENT,
          '{"plantId":<plant with stock 10, price 25.00>,"quantity":2}',
          '201 Created, message "Purchase completed successfully.", totalPrice 50.00, plant stock becomes 8', PRE)
def _(ctx):
    p = ctx.plant(quantity=10, price=25.00)
    s, b = buy(ctx.client, p["id"], 2)
    return verify(s, b, 201, "Purchase completed successfully.",
                  checks=[("total 50.00", lambda: float(b["data"]["totalPrice"]) == 50.0),
                          ("stock 8", lambda: ctx.get_plant(p["id"])["quantity"] == 8)])


@api_test("TC_API_M5_02", M, "Purchase quantity 0 is rejected", BUY, CLIENT, '{"plantId":<id>,"quantity":0}',
          '400 Bad Request, errors.quantity = "Quantity must be greater than 0"', PRE)
def _(ctx):
    p = ctx.plant()
    s, b = buy(ctx.client, p["id"], 0)
    return verify(s, b, 400, field="quantity", field_msg="Quantity must be greater than 0")


@api_test("TC_API_M5_03", M, "Purchase quantity above stock is rejected, stock unchanged", BUY, CLIENT,
          '{"plantId":<plant with stock 3>,"quantity":4}',
          '400 Bad Request, "Only 3 items available in stock"; plant stock remains 3',
          "A Client is logged in; a plant with stock 3 exists.")
def _(ctx):
    p = ctx.plant(quantity=3)
    s, b = buy(ctx.client, p["id"], 4)
    return verify(s, b, 400, checks=[("message", lambda: "Only 3 items available in stock" in str(b)),
                                     ("stock 3", lambda: ctx.get_plant(p["id"])["quantity"] == 3)])


@api_test("TC_API_M5_04", M, "Buying an out-of-stock plant is rejected", BUY, CLIENT,
          '{"plantId":<plant with stock 0>,"quantity":1}', '409 Conflict, "This plant is out of stock"',
          "A Client is logged in; a plant with stock 0 exists.")
def _(ctx):
    p = ctx.plant(quantity=0)
    s, b = buy(ctx.client, p["id"], 1)
    return verify(s, b, 409, checks=[("message", lambda: "This plant is out of stock" in str(b))])


@api_test("TC_API_M5_05", M, "Buying a non-existing plant", BUY, CLIENT, '{"plantId":99999999,"quantity":1}',
          '400 Bad Request, errors.plantId = "Plant not found" (field rule "Plant must exist", SRS 6.5.2/4.7)',
          "A Client is logged in.")
def _(ctx):
    s, b = buy(ctx.client, 99999999, 1)
    return verify(s, b, 400, field="plantId", field_msg="Plant not found")


@api_test("TC_API_M5_06", M, "Decimal purchase quantity is rejected", BUY, CLIENT, '{"plantId":<id>,"quantity":1.5}',
          '400 Bad Request, errors.quantity = "Quantity must be a whole number"', PRE)
def _(ctx):
    p = ctx.plant()
    s, b = buy(ctx.client, p["id"], 1.5)
    return verify(s, b, 400, field="quantity", field_msg="Quantity must be a whole number")


@api_test("TC_API_M5_07", M, "Quantity sent as text is accepted", BUY, CLIENT, '{"plantId":<id>,"quantity":"2"}',
          '201 Created, message "Purchase completed successfully.", quantity 2', PRE)
def _(ctx):
    p = ctx.plant()
    s, b = buy(ctx.client, p["id"], "2")
    return verify(s, b, 201, "Purchase completed successfully.",
                  checks=[("qty 2", lambda: b["data"]["quantity"] == 2)])


@api_test("TC_API_M5_08", M, "Purchase without a token is rejected", BUY, "No token",
          '{"plantId":<id>,"quantity":1}', '401 Unauthorized, message "Authentication required"')
def _(ctx):
    s, b = call("POST", "/api/client/purchases", {"plantId": 1, "quantity": 1})
    return verify(s, b, 401, "Authentication required")


@api_test("TC_API_M5_09", M, "Admin token cannot use the Client purchase API", BUY, "Admin token",
          '{"plantId":<id>,"quantity":1}',
          '403 Forbidden, message "You do not have permission to access this resource"')
def _(ctx):
    p = ctx.plant()
    s, b = buy(ctx.admin, p["id"], 1)
    return verify(s, b, 403, "You do not have permission to access this resource")


@api_test("TC_API_M5_10", M, "My Purchases shows only the logged-in Client's purchases",
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


@api_test("TC_API_M5_11", M, "Purchase keeps the unit price at the time of purchase",
          "GET /api/client/purchases", CLIENT,
          "Buy plant at 20.00; Admin changes price to 35.00; list purchases",
          "200 OK, purchase still shows unitPrice 20.00", PRE)
def _(ctx):
    cl = ctx.new_client()
    p = ctx.plant(price=20.00)
    ctx.buy(cl["token"], p["id"], 1)
    call("PUT", f"/api/admin/plants/{p['id']}", {"name": p["name"], "categoryId": p["categoryId"],
                                                  "price": 35.00, "quantity": p["quantity"] - 1}, ctx.admin)
    s, b = call("GET", "/api/client/purchases", token=cl["token"])
    return verify(s, b, 200, checks=[("unitPrice 20.00", lambda: float(b["data"]["content"][0]["unitPrice"]) == 20.0)])


@api_test("TC_API_M5_12", M, "Buy Plant page data shows the exact available stock",
          "GET /api/client/plants/{id}/buy-info", CLIENT, "Plant with quantity 7",
          '200 OK, availableStock 7, outOfStock false', "A Client is logged in; a plant with stock 7 exists.")
def _(ctx):
    p = ctx.plant(quantity=7)
    s, b = call("GET", f"/api/client/plants/{p['id']}/buy-info", token=ctx.client)
    return verify(s, b, 200, checks=[("stock 7", lambda: b["data"]["availableStock"] == 7),
                                     ("outOfStock false", lambda: b["data"]["outOfStock"] is False)])


@api_test("TC_API_M5_13", M, "Get logged-in Client account details", "GET /api/client/me", CLIENT,
          "Token of default Client 'user'",
          '200 OK, username "user", role CLIENT, no password field in response')
def _(ctx):
    s, b = call("GET", "/api/client/me", token=ctx.client)
    return verify(s, b, 200, checks=[("username user", lambda: b["data"]["username"] == "user"),
                                     ("no password", lambda: "password" not in str(b).lower())])


@api_test("TC_API_M5_14", M, "Client token is invalid after logout", "POST /api/client/auth/logout", CLIENT,
          "Fresh Client token; then GET /api/client/purchases with same token",
          'Logout 200; next call 401, message "Invalid or expired token"',
          steps="1. Log in as a Client and copy the token.\n2. Send POST /api/client/auth/logout.\n"
                "3. Send GET /api/client/purchases with the same token.\n4. Check status and message.")
def _(ctx):
    t = login_client()
    s1, _b = call("POST", "/api/client/auth/logout", token=t)
    s, b = call("GET", "/api/client/purchases", token=t)
    return verify(s, b, 401, "Invalid or expired token", checks=[("logout 200", lambda: s1 == 200)])


@api_test("TC_API_M5_15", M, "Token of a deactivated Client is rejected", "GET /api/client/purchases",
          "Token of a Client later deactivated", "Client logs in; Admin deactivates the Client; Client lists purchases",
          '401 Unauthorized, message "Your account is inactive. Please contact support."',
          "A Client is logged in.")
def _(ctx):
    cl = ctx.new_client()
    call("PATCH", f"/api/admin/users/{cl['id']}/deactivate", token=ctx.admin)
    s, b = call("GET", "/api/client/purchases", token=cl["token"])
    return verify(s, b, 401, "Your account is inactive. Please contact support.")
