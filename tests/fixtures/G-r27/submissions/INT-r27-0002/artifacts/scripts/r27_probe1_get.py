#!/usr/bin/env python3
# INT-r27-0002 script1: GET dictionary spray vs http://svc-shop:8001
import json, urllib.request, urllib.error, time, re

BASE = "http://svc-shop:8001"

PATHS = [
    # credential family
    "/login", "/signin", "/api/login", "/register", "/signup", "/api/register",
    "/forgot", "/reset", "/api/reset", "/password-reset", "/token", "/api/token",
    "/oauth/token", "/auth", "/logout", "/session", "/me",
    # info family
    "/debug/env", "/debug/vars", "/actuator/env", "/metrics", "/.env", "/info",
    "/graphql", "/health", "/status", "/version",
    # ssrf family
    "/fetch", "/preview", "/proxy", "/render", "/template",
    # processor family
    "/unserialize", "/deserialize", "/decode", "/import", "/upload", "/export",
    "/xml", "/api/xml",
    # resource-param family
    "/item", "/order", "/product", "/detail", "/invoice", "/user", "/account",
    # xss family
    "/search", "/echo", "/comment", "/reply", "/feedback", "/q", "/report",
    # file family
    "/download", "/file", "/read", "/static", "/files",
    # cors family
    "/cors", "/cors-debug", "/origin",
    # redirect family
    "/redirect", "/goto", "/jump", "/out", "/link",
    # admin family
    "/admin", "/manage", "/console", "/admin/config", "/admin/logs", "/admin/keys",
    "/admin/reports", "/admin/clients", "/admin/audit", "/admin/settings", "/admin/users",
    # ssti/cmdi family (dedup: /render already above)
    "/exec", "/run", "/eval", "/ping", "/api",
    # version/internal family
    "/api/v2", "/internal", "/private", "/api/v1",
]

INTERESTING_HEADERS = [
    "Content-Type", "Location", "Access-Control-Allow-Origin",
    "Access-Control-Allow-Credentials", "Access-Control-Allow-Methods",
    "Access-Control-Allow-Headers", "WWW-Authenticate", "Allow", "Set-Cookie",
    "Server", "X-Powered-By", "X-Frame-Options", "CORS", "Vary",
]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def probe(path):
    url = BASE + path
    entry = {"path": path, "method": "GET"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "r27-recon/1.0"})
        resp = opener.open(req, timeout=5)
        body_b = resp.read(4096)
        entry["status"] = resp.status
        hdrs = {k: v for k, v in resp.headers.items() if k in INTERESTING_HEADERS}
        entry["headers"] = hdrs
        text = body_b.decode("utf-8", "replace")
        entry["len"] = len(body_b)
        entry["body_head"] = text[:400]
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        if m:
            entry["title"] = m.group(1).strip()[:120]
    except urllib.error.HTTPError as e:
        try:
            body_b = e.read(4096)
        except Exception:
            body_b = b""
        entry["status"] = e.code
        hdrs = {k: v for k, v in e.headers.items() if k in INTERESTING_HEADERS}
        entry["headers"] = hdrs
        text = body_b.decode("utf-8", "replace")
        entry["len"] = len(body_b)
        entry["body_head"] = text[:400]
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        if m:
            entry["title"] = m.group(1).strip()[:120]
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
    return entry

results = []
for p in PATHS:
    results.append(probe(p))
    time.sleep(0.2)

summary = {"base": BASE, "total": len(results), "results": results}
print(json.dumps(summary, ensure_ascii=False, indent=1))
