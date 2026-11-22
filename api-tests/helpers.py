"""Small request-body helpers shared by the member test files."""
from client import call


def plant_body(ctx, **over):
    """Valid Add Plant body in a fresh sub-category; override any field."""
    b = {"name": "Plant " + ctx.uniq(8), "categoryId": ctx.sub_cat()["id"], "price": 25.00, "quantity": 10}
    b.update(over)
    return b


def reg_body(ctx, **over):
    """Valid registration body with a unique username/email; override any field."""
    u = "r_" + ctx.uniq(8).lower()
    b = {"fullName": "John Perera", "email": f"{u}@example.com", "username": u,
         "password": "Passw0rd1", "confirmPassword": "Passw0rd1"}
    b.update(over)
    return b


def post_reg(b):
    return call("POST", "/api/client/public/auth/register", b)


def content(b):
    return b["data"]["content"]


def buy(token, pid, qty):
    return call("POST", "/api/client/purchases", {"plantId": pid, "quantity": qty}, token)


def sell(ctx, body):
    return call("POST", "/api/admin/sales", body, ctx.admin)
