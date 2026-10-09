#!/usr/bin/env python3
# INT-r27-0005 script1: GET dictionary spray on http://svc-login:8004 (no redirect, timeout 5s, interval 0.2s)
import urllib.request, urllib.error, time, json

BASE = "http://svc-login:8004"
UA = "Mozilla/5.0 (compatible; recon/1.0)"

FAMILIES = {
    "cred": ["/login", "/signin", "/api/login", "/register", "/signup", "/api/register",
             "/forgot", "/reset", "/api/reset", "/password-reset", "/token", "/api/token",
             "/oauth/token", "/auth", "/logout", "/session", "/me", "/sessions"],
    "info": ["/debug/env", "/debug/vars", "/actuator/env", "/metrics", "/.env", "/info",
             "/graphql", "/health", "/status", "/version"],
    "ssrf": ["/fetch", "/preview", "/proxy", "/render", "/template"],
    "processor": ["/unserialize", "/deserialize", "/decode", "/import", "/upload", "/export", "/xml"],
    "resource": ["/item", "/order", "/product", "/detail", "/invoice", "/user", "/account", "/users"],
    "xss": ["/search", "/echo", "/comment", "/reply", "/feedback", "/q", "/report"],
    "file": ["/download", "/file", "/read", "/static", "/files"],
    "cors": ["/cors", "/cors-debug", "/origin"],
    "redirect": ["/redirect", "/goto", "/jump", "/out", "/link"],
    "admin": ["/admin", "/manage", "/console", "/admin/config", "/admin/logs", "/admin/keys",
              "/admin/reports", "/admin/clients", "/admin/audit", "/admin/settings", "/admin/users"],
    "internal": ["/api", "/api/v1", "/api/v2", "/internal", "/private"],
}

KEY_HEADERS = ["Content-Type", "Location", "Set-Cookie", "WWW-Authenticate", "X-Auth-Token",
               "Allow", "Server", "Content-Length", "Access-Control-Allow-Origin"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

results = []
total = sum(len(v) for v in FAMILIES.values())
n = 0
for fam, paths in FAMILIES.items():
    for p in paths:
        n += 1
        url = BASE + p
        rec = {"family": fam, "path": p}
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
        try:
            r = opener.open(req, timeout=5)
            body = r.read(4096)
            rec["status"] = r.status
            hdrs = {k: v for k, v in r.headers.items()}
            rec["headers"] = {k: hdrs[k] for k in KEY_HEADERS if k in hdrs}
            rec["body_head"] = body[:400].decode("utf-8", "replace")
            rec["body_len"] = len(body)
        except urllib.error.HTTPError as e:
            rec["status"] = e.code
            hdrs = {k: v for k, v in e.headers.items()} if e.headers else {}
            rec["headers"] = {k: hdrs[k] for k in KEY_HEADERS if k in hdrs}
            try:
                b = e.read(4096)
                rec["body_head"] = b[:400].decode("utf-8", "replace")
                rec["body_len"] = len(b)
            except Exception:
                rec["body_head"] = ""
                rec["body_len"] = 0
        except Exception as e:
            rec["error"] = "%s: %s" % (type(e).__name__, e)
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        time.sleep(0.2)

non404 = [r for r in results if r.get("status") is not None and r["status"] != 404]
print(json.dumps({"summary": "get-dict-done", "total": total,
                  "non404_count": len(non404),
                  "non404": ["%s%s -> %s" % (BASE, r["path"], r["status"]) for r in non404]},
                 ensure_ascii=False), flush=True)
