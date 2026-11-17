"""M4 - Plant Catalog, Plant Details, public categories, list rules (SRS 7.3, 7.4, 4.8, 4.2)."""
from client import call
from framework import api_test, verify

M = "M4"
CAT = "GET /api/client/public/plants"
NONE = "No token (Guest)"


def content(b):
    return b["data"]["content"]


@api_test("TC_API_M4_01", M, "Guest can view the plant catalog with default page size 12", CAT, NONE,
          "No query parameters", '200 OK, message "Plants retrieved successfully", data.size = 12')
def _(ctx):
    s, b = call("GET", "/api/client/public/plants")
    return verify(s, b, 200, checks=[("size 12", lambda: b["data"]["size"] == 12),
                                     ("success true", lambda: b["success"] is True)])


@api_test("TC_API_M4_02", M, "Search by partial, case-insensitive plant name",
          "GET /api/client/public/plants?search={part}", NONE,
          'Plant "Plant <XXXX>"; search = lowercase middle part of the name',
          "200 OK, the plant is in the result list", "A plant exists.")
def _(ctx):
    p = ctx.plant()
    part = p["name"][7:12].lower()
    s, b = call("GET", f"/api/client/public/plants?search={part}")
    return verify(s, b, 200, checks=[("plant found", lambda: p["id"] in [x["id"] for x in content(b)])])


@api_test("TC_API_M4_03", M, "Filter by main category shows plants of all sub-categories",
          "GET /api/client/public/plants?categoryId={mainId}", NONE,
          "Main category with 2 sub-categories, 1 plant each", "200 OK, both plants returned (totalElements 2)",
          "A main category with two sub-categories, each with one plant.")
def _(ctx):
    main = ctx.main_cat()
    a = ctx.plant(category_id=ctx.sub_cat(main["id"])["id"])
    c = ctx.plant(category_id=ctx.sub_cat(main["id"])["id"])
    s, b = call("GET", f"/api/client/public/plants?categoryId={main['id']}")
    return verify(s, b, 200, checks=[("both plants", lambda: {x["id"] for x in content(b)} == {a["id"], c["id"]})])


@api_test("TC_API_M4_04", M, "Sort catalog by price descending",
          "GET /api/client/public/plants?categoryId={subId}&sortBy=price&sortDir=desc", NONE,
          "3 plants priced 10.00, 30.00, 20.00 in one sub-category",
          "200 OK, prices returned in order 30.00, 20.00, 10.00", "Three plants in one sub-category.")
def _(ctx):
    sub = ctx.sub_cat()
    for pr in (10, 30, 20):
        ctx.plant(price=pr, category_id=sub["id"])
    s, b = call("GET", f"/api/client/public/plants?categoryId={sub['id']}&sortBy=price&sortDir=desc")
    return verify(s, b, 200, checks=[("order 30,20,10",
                                      lambda: [float(x["price"]) for x in content(b)] == [30.0, 20.0, 10.0])])


@api_test("TC_API_M4_05", M, "Invalid sortBy value is rejected",
          "GET /api/client/public/plants?sortBy=quantity", NONE, "sortBy = quantity",
          '400 Bad Request, message starts with "Invalid sortBy value. Allowed: "')
def _(ctx):
    s, b = call("GET", "/api/client/public/plants?sortBy=quantity")
    return verify(s, b, 400, checks=[("message prefix",
                                      lambda: "Invalid sortBy value. Allowed: " in str(b))])


@api_test("TC_API_M4_06", M, "Page 0 is rejected", "GET /api/client/public/plants?page=0", NONE,
          "page = 0", '400 Bad Request, "Page must be 1 or greater"')
def _(ctx):
    s, b = call("GET", "/api/client/public/plants?page=0")
    return verify(s, b, 400, checks=[("message", lambda: "Page must be 1 or greater" in str(b))])


@api_test("TC_API_M4_07", M, "Page size above 100 is rejected", "GET /api/client/public/plants?size=101", NONE,
          "size = 101", '400 Bad Request, "Size must be between 1 and 100"')
def _(ctx):
    s, b = call("GET", "/api/client/public/plants?size=101")
    return verify(s, b, 400, checks=[("message", lambda: "Size must be between 1 and 100" in str(b))])


@api_test("TC_API_M4_08", M, "Out-of-stock plant shows 'Out of Stock' and cannot be bought",
          "GET /api/client/public/plants/{id}", NONE, "Plant with quantity 0",
          '200 OK, stockLabel "Out of Stock", canBuy false, exact quantity not revealed',
          "A plant with quantity 0 exists.")
def _(ctx):
    p = ctx.plant(quantity=0)
    s, b = call("GET", f"/api/client/public/plants/{p['id']}")
    d = lambda: b["data"]  # noqa: E731
    return verify(s, b, 200, checks=[("label Out of Stock", lambda: d()["stockLabel"] == "Out of Stock"),
                                     ("canBuy false", lambda: d()["canBuy"] is False),
                                     ("quantity hidden", lambda: d().get("availableQuantity") in (None,))])


@api_test("TC_API_M4_09", M, "Low-stock plant (3) shows 'Only 3 left'",
          "GET /api/client/public/plants/{id}", NONE, "Plant with quantity 3",
          '200 OK, stockLabel "Only 3 left", availableQuantity 3, canBuy true', "A plant with quantity 3 exists.")
def _(ctx):
    p = ctx.plant(quantity=3)
    s, b = call("GET", f"/api/client/public/plants/{p['id']}")
    d = lambda: b["data"]  # noqa: E731
    return verify(s, b, 200, checks=[("label Only 3 left", lambda: d()["stockLabel"] == "Only 3 left"),
                                     ("qty 3", lambda: d()["availableQuantity"] == 3),
                                     ("canBuy true", lambda: d()["canBuy"] is True)])


@api_test("TC_API_M4_10", M, "In-stock plant (10) does not reveal stock quantity",
          "GET /api/client/public/plants/{id}", NONE, "Plant with quantity 10",
          '200 OK, stockLabel "In Stock", quantity not present in response', "A plant with quantity 10 exists.")
def _(ctx):
    p = ctx.plant(quantity=10)
    s, b = call("GET", f"/api/client/public/plants/{p['id']}")
    d = lambda: b["data"]  # noqa: E731
    return verify(s, b, 200, checks=[("label In Stock", lambda: d()["stockLabel"] == "In Stock"),
                                     ("quantity hidden", lambda: d().get("availableQuantity") is None
                                      and "10" not in str(d().get("quantity", "")))])


@api_test("TC_API_M4_11", M, "Plant details show category as 'Parent > Sub-category'",
          "GET /api/client/public/plants/{id}", NONE, "Existing plant id",
          '200 OK, message "Plant retrieved successfully", categoryPath = "<Parent> > <Sub>"', "A plant exists.")
def _(ctx):
    main = ctx.main_cat()
    sub = ctx.sub_cat(main["id"])
    p = ctx.plant(category_id=sub["id"])
    s, b = call("GET", f"/api/client/public/plants/{p['id']}")
    return verify(s, b, 200, "Plant retrieved successfully",
                  checks=[("categoryPath", lambda: b["data"]["categoryPath"] == f"{main['name']} > {sub['name']}")])


@api_test("TC_API_M4_12", M, "Plant details for a non-existing id", "GET /api/client/public/plants/{id}", NONE,
          "id = 99999999", '404 Not Found, message "Plant not found"')
def _(ctx):
    s, b = call("GET", "/api/client/public/plants/99999999")
    return verify(s, b, 404, "Plant not found")


@api_test("TC_API_M4_13", M, "Catalog filter lists main categories with their sub-categories",
          "GET /api/client/public/categories", NONE, "Main category with 1 sub-category",
          "200 OK, main category appears with the sub-category in subCategories",
          "A main category with one sub-category exists.")
def _(ctx):
    main = ctx.main_cat()
    sub = ctx.sub_cat(main["id"])
    s, b = call("GET", "/api/client/public/categories")
    entry = lambda: next(x for x in b["data"] if x["id"] == main["id"])  # noqa: E731
    return verify(s, b, 200, checks=[("sub listed", lambda: sub["id"] in [x["id"] for x in entry()["subCategories"]]),
                                     ("sub not top-level", lambda: sub["id"] not in [x["id"] for x in b["data"]])])


@api_test("TC_API_M4_14", M, "Invalid token on a public API is treated as Guest", CAT,
          "Invalid token (Bearer abc.def.ghi)", "Authorization: Bearer abc.def.ghi",
          "200 OK, catalog returned (request handled as Guest)")
def _(ctx):
    s, b = call("GET", "/api/client/public/plants", token="abc.def.ghi")
    return verify(s, b, 200)


@api_test("TC_API_M4_15", M, "'%' in search is treated as a normal character",
          "GET /api/client/public/plants?search=%25", NONE,
          'One plant named "Rose%<XXXX>"; search = "%"',
          "200 OK, only plants whose name contains '%' are returned", "A plant with '%' in its name exists.")
def _(ctx):
    p = ctx.plant(name="Rose%" + ctx.uniq(6))
    s, b = call("GET", "/api/client/public/plants?search=%25&size=100")
    return verify(s, b, 200, checks=[("plant found", lambda: p["id"] in [x["id"] for x in content(b)]),
                                     ("all contain %", lambda: all("%" in x["name"] for x in content(b)))])
