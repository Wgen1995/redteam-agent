#!/usr/bin/env python3
# INT-r27-0002 script2: POST shape probe (urlencoded t=1 and JSON {"t":1}), no creds no payloads
import json, urllib.request, urllib.error, time

BASE = "http://svc-shop:8001"

PATHS = [
    # mandated minimum
    "/login", "/register", "/token", "/upload", "/import", "/xml", "/fetch",
    "/search", "/comment",
    # discovered active faces (behavior under POST)
    "/item", "/order", "/reply", "/feedback", "/logout", "/admin/reports",
]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def post(path, body_b, ctype):
    url = BASE + path
    entry = {"path": path, "method": "POST", "content_type": ctype}
    try:
        req = urllib.request.Request(url, data=body_b, method="POST", headers={
            "User-Agent": "r27-recon/1.0",
            "Content-Type": ctype,
        })
        resp = opener.open(req, timeout=5)
        body_b2 = resp.read(4096)
        entry["status"] = resp.status
        entry["headers"] = {k: v for k, v in resp.headers.items()
                            if k in ("Content-Type", "Location", "Allow",
                                     "Access-Control-Allow-Origin", "WWW-Authenticate")}
        entry["len"] = len(body_b2)
        entry["body_head"] = body_b2.decode("utf-8", "replace")[:400]
    except urllib.error.HTTPError as e:
        try:
            body_b2 = e.read(4096)
        except Exception:
            body_b2 = b""
        entry["status"] = e.code
        entry["headers"] = {k: v for k, v in e.headers.items()
                            if k in ("Content-Type", "Location", "Allow",
                                     "Access-Control-Allow-Origin", "WWW-Authenticate")}
        entry["len"] = len(body_b2)
        entry["body_head"] = body_b2.decode("utf-8", "replace")[:400]
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
    return entry

results = []
for p in PATHS:
    results.append(post(p, b"t=1", "application/x-www-form-urlencoded"))
    time.sleep(0.2)
    results.append(post(p, b'{"t":1}', "application/json"))
    time.sleep(0.2)

print(json.dumps({"base": BASE, "total": len(results), "results": results},
                 ensure_ascii=False, indent=1))
