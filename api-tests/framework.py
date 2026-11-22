"""Minimal test-case registry + fixtures for the QA Training App API tests.

Each API test case is a function decorated with @api_test(...). The decorator
stores the documentation fields (used to build the Excel test case document)
and the function performs the request and returns verify(...).
"""
import json, random, string
from dataclasses import dataclass, field
from client import call, login_admin, login_client

REGISTRY = []


class Blocked(Exception):
    """Raised when a precondition (fixture) cannot be set up."""


@dataclass
class Result:
    passed: bool
    actual: str


def api_test(tc_id, member, title, endpoint, role, data, expected,
             precondition="Application is running; default accounts exist.",
             steps=None, description=None):
    def deco(fn):
        method, path = endpoint.split(" ", 1)
        REGISTRY.append({
            "id": tc_id, "member": member, "title": title,
            "description": description or title,
            "endpoint": endpoint, "role": role, "data": data,
            "expected": expected, "precondition": precondition,
            "steps": steps or (
                f"1. Send {method} {path} using {role}.\n"
                f"2. Send the test data as the request.\n"
                f"3. Check the HTTP status code and the response body."),
            "fn": fn,
        })
        return fn
    return deco


def short(b):
    if not isinstance(b, dict):
        return str(b)[:200]
    out = f"message='{b.get('message')}'"
    if b.get("errors"):
        out += f", errors={json.dumps(b['errors'])}"
    return out


def verify(status, body, exp_status, exp_message=None, field=None,
           field_msg=None, checks=()):
    """Compare a response with the expected result.

    checks: iterable of (description, callable -> bool).
    """
    problems = []
    if status != exp_status:
        problems.append(f"status {status} != {exp_status}")
    msg = body.get("message") if isinstance(body, dict) else None
    if exp_message is not None and msg != exp_message:
        problems.append(f"message '{msg}' != '{exp_message}'")
    if field is not None:
        got = (body.get("errors") or {}).get(field) if isinstance(body, dict) else None
        if got != field_msg:
            problems.append(f"errors.{field} '{got}' != '{field_msg}'")
    for desc, fn in checks:
        try:
            ok = fn()
        except Exception as e:  # noqa: BLE001
            ok, desc = False, f"{desc} ({type(e).__name__}: {e})"
        if not ok:
            problems.append(f"check failed: {desc}")
    actual = f"{status}, {short(body)}"
    if problems:
        actual += " | MISMATCH: " + "; ".join(problems)
    return Result(not problems, actual)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
class Ctx:
    def __init__(self):
        self.admin = login_admin()
        self.client = login_client()

    # random suffixes keep every run independent (names must be unique)
    @staticmethod
    def uniq(n=5):
        return "".join(random.choices(string.ascii_uppercase, k=n))

    def _ok(self, status, body, what, expected=(200, 201)):
        if status not in expected:
            raise Blocked(f"Precondition failed - {what}: {status} {short(body)}")
        return body["data"] if isinstance(body, dict) and "data" in body else body

    def main_cat(self):
        s, b = call("POST", "/api/admin/categories",
                    {"name": "M" + self.uniq(6), "parentId": None}, self.admin)
        return self._ok(s, b, "create main category")

    def sub_cat(self, parent_id=None):
        parent_id = parent_id or self.main_cat()["id"]
        s, b = call("POST", "/api/admin/categories",
                    {"name": "S" + self.uniq(6), "parentId": parent_id}, self.admin)
        return self._ok(s, b, "create sub-category")

    def plant(self, quantity=10, price=25.00, category_id=None, name=None):
        category_id = category_id or self.sub_cat()["id"]
        s, b = call("POST", "/api/admin/plants",
                    {"name": name or "Plant " + self.uniq(8), "categoryId": category_id,
                     "price": price, "quantity": quantity}, self.admin)
        return self._ok(s, b, "create plant")

    def get_plant(self, pid):
        s, b = call("GET", f"/api/admin/plants/{pid}", token=self.admin)
        return self._ok(s, b, "get plant")

    def new_client(self, login=True):
        u = "u_" + self.uniq(8).lower()
        pw = "Passw0rd1"
        s, b = call("POST", "/api/client/public/auth/register", {
            "fullName": "Test " + u, "email": f"{u}@mail.com", "username": u,
            "password": pw, "confirmPassword": pw})
        data = self._ok(s, b, "register client")
        token = login_client(u, pw) if login else None
        return {"id": data["id"], "username": u, "password": pw, "token": token,
                "email": f"{u}@mail.com"}

    def buy(self, token, plant_id, qty=1):
        s, b = call("POST", "/api/client/purchases",
                    {"plantId": plant_id, "quantity": qty}, token)
        return self._ok(s, b, "client purchase")

    def sell(self, plant_id, qty=1):
        s, b = call("POST", "/api/admin/sales",
                    {"plantId": plant_id, "quantity": qty}, self.admin)
        return self._ok(s, b, "admin sale")


def parallel(*fns):
    """Run the given zero-argument callables at the same moment; return their results in order.

    Used by the "parallel" test cases (SRS rules that break only when requests arrive together).
    In Postman the same thing is done with the Collection Runner (several iterations, no delay).
    """
    import threading
    out = [None] * len(fns)
    barrier = threading.Barrier(len(fns))

    def run(i):
        barrier.wait()
        out[i] = fns[i]()
    threads = [threading.Thread(target=run, args=(i,)) for i in range(len(fns))]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return out
