"""Tiny HTTP helper for the QA Training App API (stdlib only)."""
import json, os, urllib.request, urllib.error

BASE = os.environ.get("QA_BASE_URL", "http://localhost:8080")


def call(method, path, body=None, token=None, raw=None, headers=None):
    """Return (status, parsed_json_or_text)."""
    h = {"Accept": "application/json"}
    data = None
    if raw is not None:
        data = raw.encode() if isinstance(raw, str) else raw
    elif body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = f"Bearer {token}"
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            status, text = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode()
    try:
        return status, json.loads(text) if text else None
    except ValueError:
        return status, text


def login_admin(u="admin", p="Admin@123"):
    s, b = call("POST", "/api/admin/auth/login", {"username": u, "password": p})
    assert s == 200, (s, b)
    return b["data"]["token"]


def login_client(u="user", p="User@123"):
    s, b = call("POST", "/api/client/public/auth/login", {"username": u, "password": p})
    assert s == 200, (s, b)
    return b["data"]["token"]
