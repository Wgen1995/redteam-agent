#!/usr/bin/env python3
"""INT-r27-0009 script 1: GET dictionary spray on http://svc-files:8008.
13 families per delegation. No redirects, timeout 5, interval 0.25s. Discovery only."""
import json, time, urllib.request, urllib.error

BASE = "http://svc-files:8008"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

FAMILIES = {
    "file": ["/download", "/file", "/read", "/static", "/files", "/assets", "/media",
             "/uploads", "/docs", "/documents", "/backup", "/archive", "/tmp",
             "/conf", "/config", "/etc"],
    "cred": ["/login", "/signin", "/api/login", "/register", "/signup", "/api/register",
             "/forgot", "/reset", "/token", "/api/token", "/auth", "/logout",
             "/session", "/me"],
    "info": ["/debug/env", "/debug/vars", "/actuator/env", "/metrics", "/.env",
             "/info", "/graphql", "/health", "/status", "/version"],
    "ssrf": ["/fetch", "/preview", "/proxy", "/render", "/template"],
    "processor": ["/unserialize", "/deserialize", "/decode", "/import", "/upload",
                  "/export", "/xml"],
    "resource": ["/item", "/order", "/product", "/detail", "/invoice", "/user",
                 "/account", "/users"],
    "xss": ["/search", "/echo", "/comment", "/reply", "/feedback", "/q", "/report"],
    "cors": ["/cors", "/cors-debug", "/origin"],
    "redirect": ["/redirect", "/goto", "/jump", "/out", "/link"],
    "admin": ["/admin", "/manage", "/console", "/admin/config", "/admin/logs",
              "/admin/keys", "/admin/reports", "/admin/clients", "/admin/audit",
              "/admin/settings", "/admin/users"],
    "apiv": ["/api", "/api/v1", "/api/v2", "/internal", "/private"],
}

BASELINE_404 = "not found"
results, dist = [], {"total": 0, "non404": 0}

for fam, paths in FAMILIES.items():
    for p in paths:
        entry = {"family": fam, "path": p}
        try:
            req = urllib.request.Request(BASE + p, headers={"User-Agent": "recon-int-r27/1.0"})
            resp = opener.open(req, timeout=5)
            body = resp.read(800)
            entry.update({"status": resp.status,
                          "headers": {k.lower(): v for k, v in resp.headers.items()
                                      if k.lower() in ("content-type", "content-length",
                                                        "location", "server", "allow",
                                                        "www-authenticate", "set-cookie")},
                          "body_head": body[:400].decode("utf-8", "replace")})
        except urllib.error.HTTPError as e:
            body = e.read(800)
            entry.update({"status": e.code,
                          "headers": {k.lower(): v for k, v in e.headers.items()
                                      if k.lower() in ("content-type", "content-length",
                                                        "location", "server", "allow",
                                                        "www-authenticate", "set-cookie")},
                          "body_head": body[:400].decode("utf-8", "replace")})
        except Exception as e:
            entry["error"] = repr(e)
        dist["total"] += 1
        if entry.get("status") != 404 or entry.get("body_head", "").strip() != BASELINE_404:
            dist["non404"] += 1
            results.append(entry)
        time.sleep(0.25)

print(json.dumps({"baseline": "GET / -> 404 'not found'",
                  "distinct_or_error": dist, "hits": results},
                 ensure_ascii=False, indent=1))
